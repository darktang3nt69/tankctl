import { z } from 'zod';

export const loginSchema = z.object({
  apiUrl: z.string()
    .min(1, { message: "API Server URL is required" })
    .refine(val => {
      try {
        new URL(val);
        return true;
      } catch (error) {
        return false;
      }
    }, { message: "Invalid URL format" }),
  apiKey: z.string().min(1, { message: "API Key is required" }),
}); 