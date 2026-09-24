import { z } from 'zod'

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const phonePattern = /^(\+?91)?[6-9]\d{9}$/

export const loginIdentifierSchema = z.string().trim().min(1, 'Enter your email or phone').refine((val) => {
  if (emailPattern.test(val)) return true
  const digits = val.replace(/[\s\-\(\)]/g, '')
  return phonePattern.test(digits) || /^\+?\d{10,13}$/.test(digits)
}, {
  message: 'Enter a valid email address or 10-digit mobile number',
})

export const loginSchema = z.object({
  email: z.string().trim().email('Enter a valid email address'),
  password: z.string().min(8, 'Use at least 8 characters'),
  remember: z.boolean().optional(),
})
export const forgotPasswordSchema = z.object({ email: z.string().trim().email('Enter a valid email address') })
export const resetPasswordSchema = z.object({ password: z.string().min(8, 'Use at least 8 characters').regex(/[A-Z]/, 'Add one uppercase letter').regex(/[0-9]/, 'Add one number'), confirmPassword: z.string() }).refine((data) => data.password === data.confirmPassword, { path: ['confirmPassword'], message: 'Passwords do not match' })
export const accountSchema = z.object({ name: z.string().trim().min(2, 'Enter your full name'), email: z.string().trim().email('Enter a valid email address'), phone: z.string().trim().min(8, 'Enter a valid phone number'), password: z.string().min(8, 'Use at least 8 characters').regex(/[A-Z]/, 'Add one uppercase letter').regex(/[0-9]/, 'Add one number'), confirmPassword: z.string() }).refine((data) => data.password === data.confirmPassword, { path: ['confirmPassword'], message: 'Passwords do not match' })
export const emailFieldSchema = z.object({ email: z.string().trim().email('Enter a valid email address') })
export type LoginValues = z.infer<typeof loginSchema>
export type ForgotPasswordValues = z.infer<typeof forgotPasswordSchema>
export type ResetPasswordValues = z.infer<typeof resetPasswordSchema>
export type AccountValues = z.infer<typeof accountSchema>
