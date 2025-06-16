import { z } from 'zod';

export const loginSchema = z.object({
  apiKey: z.string().min(1, { message: "API Key is required" }),
}); 