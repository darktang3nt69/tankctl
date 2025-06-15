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

// Mock localStorage
const localStorageMock = (() => {
  let store: { [key: string]: string } = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: jest.fn((key: string) => { delete store[key]; }),
    clear: jest.fn(() => { store = {}; }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('LoginForm validation', () => {
  const mockLogin = login as jest.Mock;
  const mockUseAuthStore = useAuthStore as jest.MockedFunction<typeof useAuthStore>;
  const mockUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;
  const mockPush = jest.fn();

  beforeEach(() => {
    mockLogin.mockClear();
    mockUseAuthStore.mockClear();
    mockUseRouter.mockClear();
    mockPush.mockClear();
    localStorageMock.clear(); // Clear localStorage mock before each test

    mockUseRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
    } as any);

    // Mock useAuthStore to return a consistent state and actions
    mockUseAuthStore.mockReturnValue({
      isAuthenticated: false,
      token: null,
      apiUrl: null,
      login: jest.fn(),
      logout: jest.fn(),
      setApiUrl: jest.fn(),
    });
  });

  it('should display error for empty API Server URL', async () => {
    render(<LoginForm />);

    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(screen.getByText(/api server url is required/i)).toBeInTheDocument();
    });
  });

  it('should display error for invalid URL format', async () => {
    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'abc' } });
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid url format/i)).toBeInTheDocument();
    });
  });

  it('should display error for empty API Key', async () => {
    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://localhost:8080' } });
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(screen.getByText(/api key is required/i)).toBeInTheDocument();
    });
  });

  it('should log in successfully with valid credentials and redirect', async () => {
    mockLogin.mockResolvedValueOnce({ success: true, token: 'mock_jwt_token' });

    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://localhost:8080' } });
    fireEvent.change(screen.getByLabelText(/admin_api_key/i), { target: { value: 'test-key' } });
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('http://localhost:8080', 'test-key');
      expect(mockUseAuthStore().login).toHaveBeenCalledWith('mock_jwt_token', 'http://localhost:8080');
      expect(mockPush).toHaveBeenCalledWith('/home');
    });
  });

  it('should display alert on failed login', async () => {
    mockLogin.mockResolvedValueOnce({ success: false, message: 'Login failed due to XYZ.' });
    jest.spyOn(window, 'alert').mockImplementation(() => {}); // Mock window.alert

    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://localhost:8080' } });
    fireEvent.change(screen.getByLabelText(/admin_api_key/i), { target: { value: 'wrong-key' } });
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('http://localhost:8080', 'wrong-key');
      expect(window.alert).toHaveBeenCalledWith('Login failed due to XYZ.');
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('should remember API URL when checkbox is checked', async () => {
    render(<LoginForm />);

    fireEvent.change(screen.getByLabelText(/api server url/i), { target: { value: 'http://remembered.com' } });
    fireEvent.change(screen.getByLabelText(/admin_api_key/i), { target: { value: 'test-key' } });
    fireEvent.click(screen.getByLabelText(/remember api url/i));
    fireEvent.click(screen.getByRole('button', { name: /authenticate/i }));

    await waitFor(() => {
      expect(localStorageMock.setItem).toHaveBeenCalledWith('rememberedApiUrl', 'http://remembered.com');
    });
  });

  it('should pre-fill API URL if remembered', async () => {
    localStorageMock.setItem('rememberedApiUrl', 'http://prefilled.com');
    
    render(<LoginForm />);

    await waitFor(() => {
      expect(screen.getByLabelText(/api server url/i)).toHaveValue('http://prefilled.com');
    });
  });

  it('should clear API URL from localStorage when checkbox is unchecked', async () => {
    localStorageMock.setItem('rememberedApiUrl', 'http://tobeunremembered.com'); // Set initial state for localStorage

    render(<LoginForm />);
    
    // Wait for the component to re-render with the pre-filled value and checked checkbox
    await waitFor(() => {
      expect(screen.getByLabelText(/remember api url/i)).toBeChecked();
    });

    // Uncheck it
    fireEvent.click(screen.getByLabelText(/remember api url/i)); 

    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('rememberedApiUrl');
    });
  });
}); 