export class DiscordApi {
  constructor({ token }) {
    this.token = token;
  }

  async request(path, options = {}) {
    const response = await fetch(`https://discord.com/api/v10${path}`, {
      ...options,
      headers: {
        Authorization: `Bot ${this.token}`,
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });

    if (response.status === 204) return null;

    const text = await response.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!response.ok) {
      const detail = typeof data === 'string' ? data : JSON.stringify(data);
      throw new Error(`Discord API error ${response.status}: ${detail}`);
    }

    return data;
  }
}
