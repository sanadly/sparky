import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from './api/client';

// Mock global fetch
const fetchMock = vi.fn();
global.fetch = fetchMock;

describe('ApiClient', () => {
    let client: ApiClient;

    beforeEach(() => {
        fetchMock.mockReset();
        client = new ApiClient();
    });

    it('should make a chat request correctly', async () => {
        const mockResponse = { reply: 'Hello' };
        fetchMock.mockResolvedValueOnce({
            ok: true,
            json: async () => mockResponse,
        });

        const response = await client.chat('user123', 'Hi');

        expect(fetchMock).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ user_id: 'user123', message: 'Hi', channel: 'web' }),
        }));
        expect(response).toEqual(mockResponse);
    });

    it('should handle API errors', async () => {
        fetchMock.mockResolvedValueOnce({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
        });

        await expect(client.chat('user123', 'Hi')).rejects.toThrow('API Error: 500 Internal Server Error');
    });
});
