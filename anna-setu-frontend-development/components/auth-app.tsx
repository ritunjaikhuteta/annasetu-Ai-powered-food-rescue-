'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import {
  ArrowLeft,
  ArrowRight,
  Bike,
  Check,
  ChevronDown,
  FileCheck2,
  HandHeart,
  Leaf,
  LockKeyhole,
  Mail,
  MapPin,
  ShieldCheck,
  Sparkles,
  Upload,
  Utensils,
  X,
} from 'lucide-react'
import { authService } from '@/lib/services/auth'
import { storageService } from '@/lib/services/storage'
import {
  dashboardPath,
  isAuthRole,
  roleMeta,
  type AuthRole,
  type RegisterPayload,
} from '@/lib/auth/types'
import {
  accountSchema,
  forgotPasswordSchema,
  loginSchema,
  resetPasswordSchema,
  type AccountValues,
  type ForgotPasswordValues,
  type LoginValues,
  type ResetPasswordValues,
} from '@/lib/auth/validation'

type RouteState = {
  role?: AuthRole
  mode: 'entry' | 'login' | 'register' | 'forgot' | 'reset' | 'verification'
  step: number
}
const icons = { donor: HandHeart, receiver: Utensils, driver: Bike }
const inputClass = 'auth-input'

function parseRoute(pathname: string): RouteState {
  const parts = pathname.split('/').filter(Boolean)
  if (parts[1] === 'forgot-password') return { mode: 'forgot', step: 1 }
  if (parts[1] === 'reset-password') return { mode: 'reset', step: 1 }
  const role = parts[1] && isAuthRole(parts[1]) ? parts[1] : undefined
  if (!role) return { mode: 'entry', step: 1 }
  if (parts[2] === 'login') return { role, mode: 'login', step: 1 }
  if (parts[2] === 'verification') return { role, mode: 'verification', step: 1 }
  const maxStepForRole = role === 'driver' ? 6 : 5
  return { role, mode: 'register', step: Math.min(maxStepForRole, Math.max(1, Number(parts[2]) || 1)) }
}

function AuthBrand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`auth-brand-story ${compact ? 'compact-story' : ''}`}>
      <div className="auth-organic auth-organic-one" />
      <div className="auth-organic auth-organic-two" />
      <Link href="/" className="auth-logo">
        <span><Leaf size={21} /></span>
        <strong>AnnaSetu</strong>
        <small>food, connected</small>
      </Link>
      {!compact && (
        <div className="auth-story-copy">
          <span className="eyebrow eyebrow-light">
            <span className="eyebrow-dot" /> A better way to share
          </span>
          <h1>Good food should<br /><em>go further.</em></h1>
          <p>
            A warm, accountable bridge between food businesses, community organizations, and the people who make delivery possible.
          </p>
          <div className="auth-story-note">
            <ShieldCheck size={18} />
            <span>
              <strong>Built for trust at every handoff.</strong>
              <small>Verification keeps food safe and impact visible.</small>
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

function AuthLayout({
  children,
  title,
  kicker,
  backHref = '/',
  onBack,
}: {
  children: React.ReactNode
  title?: string
  kicker?: string
  backHref?: string
  onBack?: () => void
}) {
  const router = useRouter()

  const handleBack = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onBack) {
      e.preventDefault()
      onBack()
      return
    }
    if (typeof window !== 'undefined' && window.history.length > 1) {
      e.preventDefault()
      router.back()
    }
  }

  return (
    <main className="auth-page">
      <AuthBrand />
      <section className="auth-panel">
        <Link href={backHref} className="auth-back" onClick={handleBack}>
          <ArrowLeft size={15} /> Back
        </Link>
        <div className="auth-panel-inner">
          {kicker && <span className="auth-kicker">{kicker}</span>}
          {title && <h2>{title}</h2>}
          {children}
        </div>
      </section>
    </main>
  )
}

function RoleEntry() {
  return (
    <AuthLayout title="How will you participate?" kicker="Start with your role" backHref="/">
      <p className="auth-lead">Choose the way you want to help good food reach the right people.</p>
      <div className="auth-role-list">
        {(['donor', 'receiver', 'driver'] as AuthRole[]).map((role) => {
          const Icon = icons[role]
          return (
            <Link className={`auth-role-card auth-role-${role}`} href={`/auth/${role}/login`} key={role}>
              <span className="auth-role-icon"><Icon size={23} /></span>
              <span>
                <strong>{roleMeta[role].label}</strong>
                <small>{roleMeta[role].shortLabel}</small>
                <em>{roleMeta[role].description}</em>
              </span>
              <ArrowRight size={18} />
            </Link>
          )
        })}
      </div>
      <p className="auth-foot-note">
        Already part of the network? <Link href="/auth/donor/login">Log in</Link>
      </p>
    </AuthLayout>
  )
}

function Field({
  label,
  error,
  ...props
}: {
  label: string
  error?: string
  type?: string
  placeholder?: string
  name?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
}) {
  return (
    <label className="auth-field">
      <span>{label}</span>
      <input className={inputClass} {...props} />
      {error && <small className="field-error">{error}</small>}
    </label>
  )
}

function LoginForm({ role }: { role: AuthRole }) {
  const router = useRouter()
  const [error, setError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { remember: true },
  })

  const onSubmit = async (values: LoginValues) => {
    setError('')
    const result = await authService.signIn(role, values.email, values.password)
    if (result.ok && result.redirect) {
      router.push(result.redirect)
    } else {
      setError(result.message)
    }
  }

  return (
    <AuthLayout title={`Welcome back, ${roleMeta[role].label.toLowerCase()}.`} kicker="Log in" backHref="/auth">
      <p className="auth-lead">Pick up where you left off. Your next good handoff is waiting.</p>
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)}>
        <Field
          label="Email address"
          type="email"
          placeholder="you@example.com"
          {...register('email')}
          error={errors.email?.message}
        />
        <label className="auth-field">
          <span>Password</span>
          <div className="password-wrap">
            <input
              className={inputClass}
              type="password"
              placeholder="Your password"
              {...register('password')}
            />
            <LockKeyhole size={16} />
          </div>
          {errors.password && <small className="field-error">{errors.password.message}</small>}
        </label>
        <div className="auth-form-row">
          <label className="check-label">
            <input type="checkbox" {...register('remember')} /> <span>Remember me</span>
          </label>
          <Link href="/auth/forgot-password">Forgot password?</Link>
        </div>
        {error && <div className="auth-error">{error}</div>}
        <button className="button button-dark auth-submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Log in'} <ArrowRight size={16} />
        </button>
      </form>
      <p className="auth-foot-note">
        New to AnnaSetu? <Link href={`/auth/${role}/register`}>Create an account</Link>
      </p>
    </AuthLayout>
  )
}

const donorSteps = ['Basic account', 'Business information', 'Business verification', 'Pickup location', 'Review and submit']
const receiverSteps = ['Organization account', 'Organization details', 'Verification documents', 'Receiving setup', 'Review and submit']
const driverSteps = ['Personal information', 'Identity verification', 'Driving information', 'Vehicle information', 'Starting location', 'Review and submit']

function UploadBox({
  label,
  optional = false,
  onUpload,
}: {
  label: string
  optional?: boolean
  onUpload?: (filename: string) => void
}) {
  const [uploadedName, setUploadedName] = useState('')
  const [statusMsg, setStatusMsg] = useState('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedName(file.name)
      setStatusMsg('File selected: ' + file.name)
      if (onUpload) onUpload(file.name)
    }
  }

  return (
    <div className="upload-box">
      <div className="upload-icon"><Upload size={17} /></div>
      <div>
        <strong>{label}</strong>
        <small>{uploadedName ? uploadedName : `${optional ? 'Optional · ' : ''}PDF, JPG or PNG up to 10 MB`}</small>
        {statusMsg && <span className="text-[10px] text-emerald-700 block mt-0.5">{statusMsg}</span>}
      </div>
      <label className="button-like cursor-pointer">
        <input type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png" onChange={handleFileChange} />
        <span className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-stone-300 rounded-lg text-xs font-semibold text-stone-700 hover:bg-stone-50">
          <FileCheck2 size={13} /> {uploadedName ? 'Change' : 'Upload'}
        </span>
      </label>
    </div>
  )
}

function SelectField({
  label,
  children,
  value,
  onChange,
}: {
  label: string
  children: React.ReactNode
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void
}) {
  return (
    <label className="auth-field">
      <span>{label}</span>
      <div className="select-wrap">
        <select className={inputClass} value={value} onChange={onChange}>
          {children}
        </select>
        <ChevronDown size={15} />
      </div>
    </label>
  )
}

function RegistrationForm({ role }: { role: AuthRole }) {
  const [step, setStep] = useState(1)
  const [submitted, setSubmitted] = useState(false)
  const [emailConfirmationRequired, setEmailConfirmationRequired] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Multi-step structured data state
  const [extraData, setExtraData] = useState<Record<string, any>>({
    businessType: 'Restaurant',
    acceptedFoodType: 'Vegetarian',
    vehicleType: 'Motorcycle',
    ownershipType: 'I own this vehicle',
  })

  const updateExtra = (field: string, val: any) => {
    setExtraData((prev) => ({ ...prev, [field]: val }))
  }

  const steps = role === 'donor' ? donorSteps : role === 'receiver' ? receiverSteps : driverSteps
  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors },
  } = useForm<AccountValues>({ resolver: zodResolver(accountSchema) })

  const maxStep = steps.length

  useEffect(() => {
    const handlePopState = () => {
      setStep((prev) => Math.max(1, prev - 1))
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const next = async () => {
    // Validate step 1 fields if on step 1
    if (step === 1) {
      const valid = await trigger()
      if (!valid) return
    }
    if (typeof window !== 'undefined') {
      window.history.pushState({ authStep: step + 1 }, '')
    }
    setStep((value) => Math.min(maxStep, value + 1))
  }

  const back = () => {
    if (step > 1) {
      if (typeof window !== 'undefined' && window.history.state?.authStep) {
        window.history.back()
      } else {
        setStep((value) => Math.max(1, value - 1))
      }
    }
  }

  const submit = async (accountValues: AccountValues) => {
    setIsSubmitting(true)
    setSubmitError('')

    const payload: RegisterPayload = {
      email: accountValues.email,
      password: accountValues.password,
      fullName: accountValues.name,
      phone: accountValues.phone,
      ...extraData,
    }

    const res = await authService.submitRegistration(role, payload)
    setIsSubmitting(false)

    if (res.ok) {
      if (res.requiresEmailConfirmation) {
        setEmailConfirmationRequired(true)
      }
      setSubmitted(true)
    } else {
      setSubmitError(res.message)
    }
  }

  if (submitted) {
    if (emailConfirmationRequired) {
      return (
        <AuthLayout title="Check your email" kicker="Account Created" backHref="/auth">
          <div className="verification-state">
            <div className="verification-icon"><Mail size={32} /></div>
            <span className="status-badge status-pending">Email Confirmation Required</span>
            <h3>Check your email</h3>
            <p className="auth-lead mt-2">
              Your AnnaSetu account has been created. We sent a confirmation link to your email. Confirm your email to continue.
            </p>
            <div className="verification-note mt-4">
              <Sparkles size={16} />
              <span>After clicking the confirmation link in your email, you will be directed to your verified portal.</span>
            </div>
            <Link className="button button-dark auth-submit mt-6" href={`/auth/${role}/login`}>
              Return to Login <ArrowRight size={16} />
            </Link>
          </div>
        </AuthLayout>
      )
    }

    return <VerificationSubmitted role={role} />
  }

  return (
    <AuthLayout
      title={`Join as a ${roleMeta[role].label.toLowerCase()}.`}
      kicker="Create your account"
      backHref="/auth"
      onBack={step > 1 ? back : undefined}
    >
      <div className="progress-head">
        <span>Step {step} of {maxStep}</span>
        <strong>{steps[step - 1]}</strong>
      </div>
      <div className="progress-bar">
        <span style={{ width: `${(step / maxStep) * 100}%` }} />
      </div>
      <div className="step-dots">
        {steps.map((item, index) => (
          <span className={index + 1 <= step ? 'active' : ''} key={item}>
            {index + 1}
          </span>
        ))}
      </div>

      <form className="auth-form auth-form-step" onSubmit={handleSubmit(submit)}>
        {step === 1 && (
          <>
            <p className="step-intro">A few details to create your secure AnnaSetu account.</p>
            <Field
              label={role === 'receiver' ? 'Organization representative name' : 'Full name'}
              placeholder={role === 'receiver' ? 'Priya Sharma' : 'Your name'}
              {...register('name')}
              error={errors.name?.message}
            />
            <Field
              label="Email address"
              type="email"
              placeholder="you@example.com"
              {...register('email')}
              error={errors.email?.message}
            />
            <Field
              label="Phone number"
              placeholder="+91 98765 43210"
              {...register('phone')}
              error={errors.phone?.message}
            />
            <Field
              label="Password"
              type="password"
              placeholder="At least 8 characters"
              {...register('password')}
              error={errors.password?.message}
            />
            <Field
              label="Confirm password"
              type="password"
              placeholder="Repeat your password"
              {...register('confirmPassword')}
              error={errors.confirmPassword?.message}
            />
          </>
        )}

        {step === 2 && (
          <StepTwo role={role} extraData={extraData} updateExtra={updateExtra} />
        )}

        {step === 3 && (
          <StepThree role={role} extraData={extraData} updateExtra={updateExtra} />
        )}

        {step === 4 && (
          <StepFour role={role} extraData={extraData} updateExtra={updateExtra} />
        )}

        {step === 5 && role === 'driver' && (
          <DriverLocationStep extraData={extraData} updateExtra={updateExtra} />
        )}

        {step === 5 && role !== 'driver' && <ReviewStep role={role} />}
        {step === 6 && <ReviewStep role={role} />}

        {submitError && <div className="auth-error">{submitError}</div>}

        {step > 1 && (
          <button type="button" className="auth-text-back" onClick={back}>
            <ArrowLeft size={14} /> Previous step
          </button>
        )}

        <button
          type={step === maxStep ? 'submit' : 'button'}
          className="button button-dark auth-submit"
          disabled={isSubmitting}
          onClick={step === maxStep ? undefined : next}
        >
          {isSubmitting
            ? 'Creating account…'
            : step === maxStep
            ? 'Submit for verification'
            : 'Continue'}
          <ArrowRight size={16} />
        </button>
      </form>
      <p className="secure-note">
        <ShieldCheck size={14} /> Your information is encrypted and only used for verification.
      </p>
    </AuthLayout>
  )
}

function StepTwo({
  role,
  extraData,
  updateExtra,
}: {
  role: AuthRole
  extraData: Record<string, any>
  updateExtra: (field: string, val: any) => void
}) {
  if (role === 'donor')
    return (
      <>
        <p className="step-intro">Tell us about the food business you represent.</p>
        <Field
          label="Business name"
          placeholder="Green Leaf Catering"
          value={extraData.businessName || ''}
          onChange={(e) => updateExtra('businessName', e.target.value)}
        />
        <SelectField
          label="Business type"
          value={extraData.businessType || 'Restaurant'}
          onChange={(e) => updateExtra('businessType', e.target.value)}
        >
          <option>Restaurant</option>
          <option>Caterer</option>
          <option>Hotel</option>
          <option>Supermarket</option>
          <option>Corporate Cafeteria</option>
          <option>Food Vendor</option>
          <option>Other</option>
        </SelectField>
      </>
    )

  if (role === 'receiver')
    return (
      <>
        <p className="step-intro">Help us understand your organization.</p>
        <Field
          label="Organization name"
          placeholder="Seva Community Kitchen"
          value={extraData.organizationName || ''}
          onChange={(e) => updateExtra('organizationName', e.target.value)}
        />
        <Field
          label="Registration number"
          placeholder="Organization registration number"
          value={extraData.registrationNumber || ''}
          onChange={(e) => updateExtra('registrationNumber', e.target.value)}
        />
        <Field
          label="NGO-DARPAN ID (where applicable)"
          placeholder="Optional ID"
          value={extraData.ngoDarpanId || ''}
          onChange={(e) => updateExtra('ngoDarpanId', e.target.value)}
        />
        <Field
          label="PAN"
          placeholder="Organization PAN"
          value={extraData.pan || ''}
          onChange={(e) => updateExtra('pan', e.target.value)}
        />
      </>
    )

  return (
    <>
      <p className="step-intro">We need identity details to keep every delivery safe.</p>
      <UploadBox label="Identity document (Aadhaar / Passport)" />
      <Field
        label="Document number"
        placeholder="e.g. Aadhaar / Govt ID number"
        value={extraData.idDocNumber || ''}
        onChange={(e) => updateExtra('idDocNumber', e.target.value)}
      />
    </>
  )
}

function StepThree({
  role,
  extraData,
  updateExtra,
}: {
  role: AuthRole
  extraData: Record<string, any>
  updateExtra: (field: string, val: any) => void
}) {
  if (role === 'donor')
    return (
      <>
        <p className="step-intro">
          Verification keeps the network trustworthy. We do not mark accounts verified automatically.
        </p>
        <Field
          label="GSTIN"
          placeholder="15-character GSTIN"
          value={extraData.gstin || ''}
          onChange={(e) => updateExtra('gstin', e.target.value)}
        />
        <Field
          label="FSSAI licence / registration number"
          placeholder="FSSAI number"
          value={extraData.fssaiNumber || ''}
          onChange={(e) => updateExtra('fssaiNumber', e.target.value)}
        />
        <UploadBox label="Business registration document" />
        <UploadBox label="FSSAI licence copy" />
      </>
    )

  if (role === 'receiver')
    return (
      <>
        <p className="step-intro">
          Upload official organization documents. Your account will remain pending until review is complete.
        </p>
        <UploadBox label="Registration certificate" />
        <UploadBox label="NGO-DARPAN proof (optional)" optional />
        <UploadBox label="Authorized representative identity proof" />
      </>
    )

  return (
    <>
      <p className="step-intro">Add driving eligibility information.</p>
      <Field
        label="Driving licence number"
        placeholder="Licence number"
        value={extraData.licenceNumber || ''}
        onChange={(e) => updateExtra('licenceNumber', e.target.value)}
      />
      <Field
        label="Licence expiry date"
        type="date"
        placeholder=""
        value={extraData.licenceExpiry || ''}
        onChange={(e) => updateExtra('licenceExpiry', e.target.value)}
      />
      <UploadBox label="Driving licence copy" />
    </>
  )
}

function StepFour({
  role,
  extraData,
  updateExtra,
}: {
  role: AuthRole
  extraData: Record<string, any>
  updateExtra: (field: string, val: any) => void
}) {
  if (role === 'donor')
    return (
      <>
        <p className="step-intro">Where should delivery partners collect surplus food?</p>
        <Field
          label="Pickup address"
          placeholder="Street, city, state"
          value={extraData.pickupAddress || ''}
          onChange={(e) => updateExtra('pickupAddress', e.target.value)}
        />
        <div className="map-placeholder">
          <MapPin size={21} />
          <span>Map location preview</span>
          <small>Address will be used for delivery partner route optimization.</small>
        </div>
      </>
    )

  if (role === 'receiver')
    return (
      <>
        <p className="step-intro">Set up how your organization receives food.</p>
        <Field
          label="Receiving address"
          placeholder="Street, city, state"
          value={extraData.receivingAddress || ''}
          onChange={(e) => updateExtra('receivingAddress', e.target.value)}
        />
        <SelectField
          label="Accepted food type"
          value={extraData.acceptedFoodType || 'Vegetarian'}
          onChange={(e) => updateExtra('acceptedFoodType', e.target.value)}
        >
          <option>Vegetarian</option>
          <option>Non-Vegetarian</option>
          <option>Both</option>
        </SelectField>
      </>
    )

  return (
    <>
      <p className="step-intro">Tell us about the vehicle you plan to use.</p>
      <SelectField
        label="Vehicle type"
        value={extraData.vehicleType || 'Motorcycle'}
        onChange={(e) => updateExtra('vehicleType', e.target.value)}
      >
        <option>Motorcycle</option>
        <option>Scooter</option>
        <option>Auto</option>
        <option>Car</option>
        <option>Van</option>
        <option>Pickup</option>
        <option>Small Truck</option>
        <option>Truck</option>
      </SelectField>
      <Field
        label="Vehicle registration number"
        placeholder="DL 01 AB 1234"
        value={extraData.vehicleNumber || ''}
        onChange={(e) => updateExtra('vehicleNumber', e.target.value)}
      />
      <SelectField
        label="Ownership type"
        value={extraData.ownershipType || 'I own this vehicle'}
        onChange={(e) => updateExtra('ownershipType', e.target.value)}
      >
        <option>I own this vehicle</option>
        <option>Vehicle belongs to someone else / organization</option>
      </SelectField>
      <UploadBox label="Registration certificate (RC)" />
      <UploadBox label="Vehicle Insurance" optional />
    </>
  )
}

function DriverLocationStep({
  extraData,
  updateExtra,
}: {
  extraData: Record<string, any>
  updateExtra: (field: string, val: any) => void
}) {
  return (
    <>
      <p className="step-intro">Tell us where you usually begin deliveries.</p>
      <Field
        label="Starting address / area"
        placeholder="Area, city, state"
        value={extraData.startingAddress || ''}
        onChange={(e) => updateExtra('startingAddress', e.target.value)}
      />
      <Field
        label="City"
        placeholder="Jaipur"
        value={extraData.city || ''}
        onChange={(e) => updateExtra('city', e.target.value)}
      />
      <div className="form-grid">
        <Field
          label="State"
          placeholder="Rajasthan"
          value={extraData.state || ''}
          onChange={(e) => updateExtra('state', e.target.value)}
        />
        <Field
          label="Postal code"
          placeholder="302001"
          value={extraData.postalCode || ''}
          onChange={(e) => updateExtra('postalCode', e.target.value)}
        />
      </div>
      <div className="map-placeholder">
        <MapPin size={21} />
        <span>Starting location preview</span>
        <small>Dispatch radius will calculate missions from this anchor point.</small>
      </div>
    </>
  )
}

function ReviewStep({ role }: { role: AuthRole }) {
  return (
    <>
      <p className="step-intro">Review your details before sending them to the AnnaSetu team.</p>
      <div className="review-card">
        <span><Check size={15} /> Account credentials</span>
        <span>
          <Check size={15} />{' '}
          {role === 'donor'
            ? 'Business information'
            : role === 'receiver'
            ? 'Organization details'
            : 'Driving and vehicle information'}
        </span>
        <span><Check size={15} /> Verification declarations</span>
        <span><Check size={15} /> Location and operating preferences</span>
      </div>
      <label className="check-label review-check">
        <input type="checkbox" required />{' '}
        <span>
          I confirm these details are accurate and I understand this account will be reviewed and remain PENDING before sensitive actions are enabled.
        </span>
      </label>
    </>
  )
}

function VerificationSubmitted({ role }: { role: AuthRole }) {
  return (
    <AuthLayout title="Verification submitted" kicker="You are almost there" backHref="/auth">
      <div className="verification-state">
        <div className="verification-icon"><ShieldCheck size={30} /></div>
        <span className="status-badge status-pending">Verification Pending</span>
        <p>
          Thanks for taking the first step as a {roleMeta[role].label.toLowerCase()}. Our team will review your information and documents.
        </p>
        <div className="verification-note">
          <Sparkles size={16} />
          <span>
            Your account will remain in PENDING status until review is complete. You can sign in to view your status.
          </span>
        </div>
        <Link className="button button-dark auth-submit" href={`/auth/${role}/login`}>
          Continue to Login <ArrowRight size={16} />
        </Link>
      </div>
    </AuthLayout>
  )
}

function ForgotPassword() {
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordValues>({ resolver: zodResolver(forgotPasswordSchema) })

  const submit = async (values: ForgotPasswordValues) => {
    setError('')
    const res = await authService.sendResetLink(values.email)
    if (res.ok) {
      setSent(true)
    } else {
      setError(res.message)
    }
  }

  return (
    <AuthLayout title="Reset your password" kicker="Account recovery" backHref="/auth">
      {sent ? (
        <div className="verification-state">
          <div className="verification-icon"><Check size={30} /></div>
          <h3>Check your inbox</h3>
          <p>If an account exists for that email, we have sent a secure reset link.</p>
          <Link className="button button-dark auth-submit" href="/auth">
            Back to login <ArrowRight size={16} />
          </Link>
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit(submit)}>
          <p className="auth-lead">
            Enter the email connected to your AnnaSetu account and we will send a secure reset link.
          </p>
          <Field
            label="Email address"
            type="email"
            placeholder="you@example.com"
            {...register('email')}
            error={errors.email?.message}
          />
          {error && <div className="auth-error">{error}</div>}
          <button className="button button-dark auth-submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending link…' : 'Send reset link'} <ArrowRight size={16} />
          </button>
        </form>
      )}
    </AuthLayout>
  )
}

function ResetPassword() {
  const router = useRouter()
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordValues>({ resolver: zodResolver(resetPasswordSchema) })

  const submit = async (values: ResetPasswordValues) => {
    setError('')
    const res = await authService.resetPassword(values.password)
    if (res.ok) {
      setDone(true)
    } else {
      setError(res.message)
    }
  }

  return (
    <AuthLayout title="Choose a new password" kicker="Secure reset" backHref="/auth">
      {done ? (
        <div className="verification-state">
          <div className="verification-icon"><Check size={30} /></div>
          <h3>Password updated</h3>
          <p>Your password is ready. You can now log in securely.</p>
          <button className="button button-dark auth-submit" onClick={() => router.push('/auth')}>
            Continue to AnnaSetu <ArrowRight size={16} />
          </button>
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit(submit)}>
          <Field
            label="New password"
            type="password"
            placeholder="At least 8 characters"
            {...register('password')}
            error={errors.password?.message}
          />
          <Field
            label="Confirm new password"
            type="password"
            placeholder="Repeat your password"
            {...register('confirmPassword')}
            error={errors.confirmPassword?.message}
          />
          {error && <div className="auth-error">{error}</div>}
          <button className="button button-dark auth-submit" disabled={isSubmitting}>
            {isSubmitting ? 'Updating…' : 'Update password'} <ArrowRight size={16} />
          </button>
        </form>
      )}
    </AuthLayout>
  )
}

function VerificationPage({ role }: { role: AuthRole }) {
  return <VerificationSubmitted role={role} />
}

export default function AuthApp({ pathname }: { pathname: string }) {
  const route = useMemo(() => parseRoute(pathname), [pathname])
  if (route.mode === 'forgot') return <ForgotPassword />
  if (route.mode === 'reset') return <ResetPassword />
  if (route.mode === 'entry') return <RoleEntry />
  if (!route.role) return <RoleEntry />
  if (route.mode === 'login') return <LoginForm role={route.role} />
  if (route.mode === 'verification') return <VerificationPage role={route.role} />
  return <RegistrationForm role={route.role} />
}
