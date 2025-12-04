import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from backend.services.email_service import EmailService
from backend.config import settings

# Mock Redis
@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    # pipeline is a synchronous method on the client, so we mock it as MagicMock
    mock.pipeline = MagicMock()
    
    pipe_mock = MagicMock()
    # execute is async
    pipe_mock.execute = AsyncMock()
    
    mock.pipeline.return_value = pipe_mock
    return mock

@pytest.fixture
def email_service(mock_redis):
    with patch("backend.services.email_service.redis.from_url", return_value=mock_redis):
        service = EmailService()
        service.redis = mock_redis # Ensure it's set
        return service

@pytest.mark.asyncio
async def test_rate_limiting_allow(email_service, mock_redis):
    # Setup: Count is 5 (below limit 10)
    mock_redis.get.return_value = "5"
    
    allowed = await email_service.check_rate_limit("test@example.com")
    
    assert allowed is True
    mock_redis.pipeline.return_value.incr.assert_called()

@pytest.mark.asyncio
async def test_rate_limiting_block(email_service, mock_redis):
    # Setup: Count is 10 (at limit)
    mock_redis.get.return_value = "10"
    
    allowed = await email_service.check_rate_limit("spammer@example.com")
    
    assert allowed is False
    # Should not increment if blocked (optional, depending on implementation, but here we return early)
    mock_redis.pipeline.return_value.incr.assert_not_called()

def test_batch_processing():
    # We need to mock imaplib
    with patch("imaplib.IMAP4_SSL") as mock_imap_cls:
        mock_imap = mock_imap_cls.return_value
        mock_imap.login.return_value = "OK"
        mock_imap.select.return_value = ("OK", [b"1"])
        
        # Return 20 email IDs
        email_ids = b" ".join([str(i).encode() for i in range(1, 21)])
        mock_imap.search.return_value = ("OK", [email_ids])
        
        service = EmailService()
        # Mock fetch to return empty to avoid parsing logic errors
        mock_imap.fetch.return_value = ("OK", [])
        
        # Call with batch size 5
        service.check_new_emails(batch_size=5)
        
        # Verify fetch was called only 5 times
        assert mock_imap.fetch.call_count == 5
