import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LoginForm } from '@/components/auth/login-form';
import { login } from '@/lib/auth/authService';
import useAuthStore from '@/store/authStore';
import { useRouter } from 'next/navigation';

// Mock the necessary modules
jest.mock('@/lib/auth/authService');
jest.mock('@/store/authStore');
jest.mock('next/navigation');

describe('Login Flow Integration', () => {
  const mockLogin = login as jest.Mock;
  const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
  const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
  const mockPush = jest.fn();

  beforeEach(() => {
    mockLogin.mockClear();
    mockUseAuthStore.mockClear();
    mockUseRouter.mockClear();
    mockPush.mockClear();

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
    } as any);

    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      token: null,
      apiUrl: null,
      login: jest.fn(),
      logout: jest.fn(),
      setApiUrl: jest.fn(),
    });
  });

  it('should log in successfully and redirect to home', async () => {
    // Mock successful login from authService
    mockLogin.mockResolvedValueOnce({ success: true, token: 'test_jwt_token' });

    render(<LoginForm />);

    // Simulate user input
    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://localhost:8080' } });
    fireEvent.change(screen.getByLabelText(/admin_api_key/i), { target: { value: 'valid-key' } });

    // Simulate form submission
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    // Assertions for successful login flow
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('http://localhost:8080', 'valid-key');
      expect(mockUseAuthStore().login).toHaveBeenCalledWith('test_jwt_token', 'http://localhost:8080');
      expect(mockPush).toHaveBeenCalledWith('/home');
    });
  });

  it('should display an alert and not redirect on failed login', async () => {
    // Mock failed login from authService
    mockLogin.mockResolvedValueOnce({ success: false, message: 'Authentication failed.' });
    jest.spyOn(window, 'alert').mockImplementation(() => {}); // Mock window.alert

    render(<LoginForm />);

    // Simulate user input
    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://localhost:8080' } });
    fireEvent.change(screen.getByLabelText(/admin_api_key/i), { target: { value: 'invalid-key' } });

    // Simulate form submission
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    // Assertions for failed login flow
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('http://localhost:8080', 'invalid-key');
      expect(window.alert).toHaveBeenCalledWith('Authentication failed.');
      expect(mockUseAuthStore().login).not.toHaveBeenCalled();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });
}); 