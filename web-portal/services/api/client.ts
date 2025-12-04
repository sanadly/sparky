export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = '/api') {
        this.baseUrl = baseUrl;
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const response = await fetch(url, { ...options, headers });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    async chat(userId: string, message: string, channel: string = 'web'): Promise<any> {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({ user_id: userId, message, channel }),
        });
    }

    async pitch(productName: string, isGreen: boolean, consumption: number): Promise<any> {
        return this.request('/pitch', {
            method: 'POST',
            body: JSON.stringify({ product_name: productName, is_green: isGreen, consumption }),
        });
    }
}

export const apiClient = new ApiClient();
