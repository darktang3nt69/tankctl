import { login, logout, isAuthenticated } from '@/lib/auth/authService';
import { getToken, removeToken, setToken } from '@/lib/auth/tokenStorage';

// Mock the tokenStorage module
jest.mock('@/lib/auth/tokenStorage', () => ({
  getToken: jest.fn(),
  setToken: jest.fn(),
  removeToken: jest.fn(),
}));

describe('authService', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    (getToken as jest.Mock).mockClear();
    (setToken as jest.Mock).mockClear();
    (removeToken as jest.Mock).mockClear();
  });

  describe('login', () => {
    it('should return success and set token on valid credentials', async () => {
      const apiUrl = 'http://testapi.com';
      const apiKey = 'test-key';

      const result = await login(apiUrl, apiKey);

      expect(result.success).toBe(true);
      expect(result.token).toBeDefined();
      expect(setToken).toHaveBeenCalledWith(result.token);
    });

    it('should return failure on invalid API Key', async () => {
      const apiUrl = 'http://testapi.com';
      const apiKey = 'wrong-key';

      const result = await login(apiUrl, apiKey);

      expect(result.success).toBe(false);
      expect(result.message).toBe('Invalid API Key or API URL.');
      expect(setToken).not.toHaveBeenCalled();
    });

    it('should return failure on invalid API URL format', async () => {
      const apiUrl = 'invalid-url';
      const apiKey = 'test-key';

      const result = await login(apiUrl, apiKey);

      expect(result.success).toBe(false);
      expect(result.message).toBe('Invalid API Key or API URL.');
      expect(setToken).not.toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should remove the token', () => {
      logout();
      expect(removeToken).toHaveBeenCalledTimes(1);
    });
  });

  describe('isAuthenticated', () => {
    it('should return true if a token is present', () => {
      (getToken as jest.Mock).mockReturnValue('mock_jwt_token_123');
      expect(isAuthenticated()).toBe(true);
    });

    it('should return false if no token is present', () => {
      (getToken as jest.Mock).mockReturnValue(null);
      expect(isAuthenticated()).toBe(false);
    });
  });
}); 