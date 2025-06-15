// lib/auth/tokenStorage.ts
import CryptoJS from 'crypto-js';

const SECRET_KEY = process.env.NEXT_PUBLIC_STORAGE_SECRET || 'default_secret_key';

export const encryptData = (data: string): string => {
  return CryptoJS.AES.encrypt(data, SECRET_KEY).toString();
};

export const decryptData = (ciphertext: string): string => {
  const bytes = CryptoJS.AES.decrypt(ciphertext, SECRET_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
};

export const setToken = (token: string): void => {
  const encrypted = encryptData(token);
  localStorage.setItem('tankctl_jwt', encrypted);
};

export const getToken = (): string | null => {
  const encrypted = localStorage.getItem('tankctl_jwt');
  return encrypted ? decryptData(encrypted) : null;
};

export const removeToken = (): void => {
  localStorage.removeItem('tankctl_jwt');
};

export const getTokenExpiration = (token: string): number => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000;
  } catch {
    return 0;
  }
};