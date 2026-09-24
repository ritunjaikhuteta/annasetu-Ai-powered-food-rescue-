'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  ArrowRight,
  Bike,
  Check,
  HandHeart,
  HeartHandshake,
  Leaf,
  Menu,
  PackageCheck,
  Route,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Utensils,
  X,
  Zap,
} from 'lucide-react'
import type { UserRole } from '@/lib/types'

const roles: { id: UserRole; label: string; description: string; icon: typeof HandHeart }[] = [
  { id: 'donor', label: 'Donor', description: 'Share surplus food from restaurants, caterers & events', icon: HandHeart },
  { id: 'receiver', label: 'Receiver', description: 'Raise food needs for shelters, NGOs & food banks', icon: Utensils },
  { id: 'driver', label: 'Delivery partner', description: 'Transport and hand off rescued meals securely', icon: Bike },
]

function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className="brand-lockup">
      <div className={`brand-mark ${light ? 'brand-mark-light' : ''}`}><Leaf size={20} strokeWidth={2.6} /></div>
      <div>
        <span className={light ? 'brand-name brand-name-light' : 'brand-name'}>AnnaSetu</span>
        <span className={light ? 'brand-tagline brand-tagline-light' : 'brand-tagline'}>food, connected</span>
      </div>
    </div>
  )
}

function Header({ onStart }: { onStart: () => void }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  return (
    <header className="site-header relative">
      <Logo />
      <nav className="desktop-nav" aria-label="Main navigation">
        <a href="#how-it-works">How it works</a>
        <a href="#impact">Our impact</a>
        <a href="#community">Community</a>
      </nav>
      <div className="header-actions">
        <Link href="/auth" className="text-button">Log in</Link>
        <button className="button button-dark button-small cursor-pointer" onClick={onStart}>
          Join AnnaSetu <ArrowRight size={15} />
        </button>
      </div>
      <button
        className="icon-button mobile-menu cursor-pointer"
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        aria-label="Toggle menu"
      >
        {mobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
      </button>

      {mobileMenuOpen && (
        <div className="absolute top-[76px] left-0 right-0 bg-[#fffdf8] border-b border-[#dce5d8] p-5 shadow-xl flex flex-col gap-3 z-40 md:hidden animate-in fade-in slide-in-from-top-2">
          <a
            href="#how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="text-stone-700 font-semibold text-sm py-1"
          >
            How it works
          </a>
          <a
            href="#impact"
            onClick={() => setMobileMenuOpen(false)}
            className="text-stone-700 font-semibold text-sm py-1"
          >
            Our impact
          </a>
          <a
            href="#community"
            onClick={() => setMobileMenuOpen(false)}
            className="text-stone-700 font-semibold text-sm py-1"
          >
            Community
          </a>
          <div className="pt-3 border-t border-stone-200 flex flex-col gap-2">
            <Link
              href="/auth"
              onClick={() => setMobileMenuOpen(false)}
              className="text-center py-2 text-stone-800 font-bold text-sm"
            >
              Log in
            </Link>
            <button
              className="button button-dark w-full text-center cursor-pointer"
              onClick={() => {
                setMobileMenuOpen(false)
                onStart()
              }}
            >
              Join AnnaSetu <ArrowRight size={15} />
            </button>
          </div>
        </div>
      )}
    </header>
  )
}

function Hero({ onStart }: { onStart: () => void }) {
  return (
    <section className="hero-shell">
      <div className="hero-copy">
        <div className="eyebrow"><span className="eyebrow-dot" /> A better way to share what matters</div>
        <h1>Good food should<br /><em>go further.</em></h1>
        <p className="hero-description">
          AnnaSetu connects surplus food with people who need it most. One verified bridge between donors, receivers, and local delivery heroes.
        </p>
        <div className="hero-actions">
          <button className="button button-primary" onClick={onStart}>
            Become part of the bridge <ArrowRight size={17} />
          </button>
          <a className="play-link" href="#how-it-works">
            <span className="play-icon">▶</span> See how it works
          </a>
        </div>
        <div className="trust-row">
          <div className="avatar-stack">
            <span className="avatar avatar-a">A</span>
            <span className="avatar avatar-b">R</span>
            <span className="avatar avatar-c">S</span>
            <span className="avatar avatar-d">+</span>
          </div>
          <span>Join <strong>2,400+</strong> people already making a difference</span>
        </div>
      </div>
      <div className="hero-art" aria-label="People sharing a meal illustration">
        <div className="sun-disc" />
        <div className="art-blob art-blob-one" />
        <div className="art-blob art-blob-two" />
        <div className="hero-card hero-card-top">
          <div className="mini-icon mini-green"><PackageCheck size={16} /></div>
          <div><strong>1,240 kg</strong><span>food rescued this month</span></div>
          <TrendingUp size={18} className="trend-icon" />
        </div>
        <div className="illustration-person person-left">
          <div className="hair hair-left" /><div className="head" /><div className="body body-left" /><div className="arm arm-left" />
        </div>
        <div className="illustration-person person-right">
          <div className="hair hair-right" /><div className="head head-right" /><div className="body body-right" /><div className="arm arm-right" />
        </div>
        <div className="meal-bowl"><div className="bowl-food">•••</div><div className="bowl-rim" /></div>
        <div className="hero-card hero-card-bottom">
          <div className="mini-icon mini-orange"><HeartHandshake size={16} /></div>
          <div><strong>18,520</strong><span>meals shared together</span></div>
        </div>
      </div>
    </section>
  )
}

function ImpactStrip() {
  return (
    <section className="impact-strip" id="impact">
      <div className="impact-intro">
        <span className="leaf-badge"><Leaf size={18} /></span>
        <div><strong>Community impact</strong><span>Demo data from a growing rescue network.</span></div>
      </div>
      <div className="impact-stat"><strong>1,240</strong><span>kg food rescued</span></div>
      <div className="impact-stat"><strong>3,720</strong><span>meals served</span></div>
      <div className="impact-stat"><strong>2.4t</strong><span>Estimated CO₂e avoided</span></div>
    </section>
  )
}

function HowItWorks() {
  const items = [
    { icon: Utensils, number: '01', title: 'NGO raises a need', text: 'A verified receiving organization shares what its community needs, when and where.' },
    { icon: HandHeart, number: '02', title: 'Donor posts surplus', text: 'Food businesses add quantity, category, storage details and a safe pickup deadline.' },
    { icon: Zap, number: '03', title: 'Eligibility + priority', text: 'Deterministic matching checks distance, ETA, quantity, expiry buffer, capacity and route feasibility.' },
    { icon: Route, number: '04', title: 'Allocation + delivery', text: 'The best feasible allocation is assigned to a verified delivery partner.' },
    { icon: ShieldCheck, number: '05', title: 'Verified handoffs', text: 'GPS, OTP and package checks confirm pickup and delivery before impact is recorded.' },
  ]
  return (
    <section className="how-section" id="how-it-works">
      <div className="section-heading">
        <div className="eyebrow"><span className="eyebrow-dot" /> The AnnaSetu way</div>
        <h2>From extra to <em>enough.</em></h2>
        <p>Food meets real need through a clear, accountable rescue workflow.</p>
      </div>
      <div className="workflow-track">
        {items.map(({ icon: Icon, number, title, text }) => (
          <div className="workflow-step" key={number}>
            <div className="workflow-node"><Icon size={19} /><span>{number}</span></div>
            <div><h3>{title}</h3><p>{text}</p></div>
          </div>
        ))}
      </div>
      <div className="algorithm-callout">
        <div className="mini-icon mini-green"><Zap size={16} /></div>
        <div>
          <strong>Food meets real need.</strong>
          <span>AnnaSetu matches available food with active NGO requirements using distance, ETA, quantity, capacity and time remaining.</span>
        </div>
      </div>
    </section>
  )
}

function LogisticsExample() {
  return (
    <section className="logistics-section">
      <div className="section-heading compact">
        <div className="eyebrow"><span className="eyebrow-dot" /> One rescue, clearly tracked</div>
        <h2>A route from surplus<br />to <em>shared impact.</em></h2>
        <p>A demo allocation showing how one donation can serve multiple nearby needs.</p>
      </div>
      <div className="logistics-flow">
        <div className="flow-card flow-source">
          <span className="flow-kicker">Donor</span>
          <strong>40 kg</strong>
          <span>vegetarian cooked meals</span>
        </div>
        <div className="flow-arrow">↓<small>matching</small></div>
        <div className="allocation-card">
          <span className="flow-kicker">Allocation</span>
          <div><span>Receiver A (Seva Community Kitchen)</span><strong>12 kg</strong></div>
          <div><span>Receiver B (Anna Sadan Charitable Trust)</span><strong>8 kg</strong></div>
          <div><span>Receiver C (Sahara Community Home)</span><strong>20 kg</strong></div>
        </div>
        <div className="flow-arrow">↓<small>route assigned</small></div>
        <div className="flow-statuses">
          <span><Bike size={15} /> Delivery partner</span>
          <span><PackageCheck size={15} /> Pickup verified</span>
          <span><ShieldCheck size={15} /> Delivery verified</span>
          <span><Leaf size={15} /> Impact recorded</span>
        </div>
      </div>
    </section>
  )
}

function TrustSection() {
  return (
    <section className="trust-section">
      <div className="trust-panel">
        <div className="trust-copy">
          <div className="eyebrow eyebrow-light"><span className="eyebrow-dot" /> Built for trust at every handoff</div>
          <h2>Good intentions,<br /><em>verified.</em></h2>
          <p>Every participant and every transfer has a clear checkpoint, so the food stays safe and the impact stays accountable.</p>
        </div>
        <div className="trust-list">
          <span><Check size={16} /> Verified food businesses</span>
          <span><Check size={16} /> Verified receiving organizations</span>
          <span><Check size={16} /> Verified delivery partners</span>
          <span><Check size={16} /> GPS + OTP handoffs</span>
          <span><Check size={16} /> Tamper-evident packaging</span>
          <span className="ai-trust"><Sparkles size={16} /> Food integrity image check <small>intelligence</small></span>
        </div>
      </div>
    </section>
  )
}

function RoleSelector({ onSelect }: { onSelect: (role: UserRole) => void }) {
  return (
    <section className="role-section" id="community">
      <div className="section-heading compact">
        <div className="eyebrow"><span className="eyebrow-dot" /> Find your place</div>
        <h2>There is a role<br />for <em>everyone.</em></h2>
      </div>
      <div className="role-grid">
        {roles.map(({ id, label, description, icon: Icon }) => (
          <button className="role-card" key={id} onClick={() => onSelect(id)}>
            <div className="role-icon"><Icon size={22} /></div>
            <span className="role-label">{label}</span>
            <span className="role-description">{description}</span>
            <ArrowRight className="role-arrow" size={18} />
          </button>
        ))}
      </div>
    </section>
  )
}

export default function AnnaSetuApp() {
  const [showRoles, setShowRoles] = useState(false)
  const router = useRouter()

  const navigateToAuth = (role?: UserRole) => {
    setShowRoles(false)
    if (role) {
      router.push(`/auth/${role}/login`)
    } else {
      router.push('/auth')
    }
  }

  const handleFindYourRoleClick = () => {
    setShowRoles(true)
  }

  return (
    <div className="landing-page">
      <Header onStart={() => navigateToAuth()} />
      <main>
        <Hero onStart={() => navigateToAuth()} />
        <ImpactStrip />
        <HowItWorks />
        <LogisticsExample />
        <TrustSection />
        <RoleSelector onSelect={(selectedRole) => navigateToAuth(selectedRole)} />
        <section className="final-cta">
          <div>
            <span className="eyebrow eyebrow-light"><span className="eyebrow-dot" /> There is room for you here</span>
            <h2>Let&apos;s make sure<br /><em>nothing good goes to waste.</em></h2>
          </div>
          <button
            type="button"
            className="button button-light cursor-pointer shadow-lg hover:shadow-xl transition-all"
            onClick={handleFindYourRoleClick}
          >
            Find your role <ArrowRight size={17} />
          </button>
        </section>
      </main>
      <footer>
        <Logo />
        <span>Built for a kinder, more connected food system.</span>
        <span>© {new Date().getFullYear()} AnnaSetu</span>
      </footer>

      {showRoles && (
        <div
          className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/60 backdrop-blur-sm"
          onClick={() => setShowRoles(false)}
        >
          <div
            className="role-modal bg-[#fffdf8] border border-[#d4e1ce] rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative text-left"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="modal-close absolute top-5 right-5 text-stone-400 hover:text-stone-700 bg-transparent border-0 cursor-pointer p-1.5 rounded-full hover:bg-stone-100 transition-colors"
              onClick={() => setShowRoles(false)}
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
            <span className="eyebrow"><span className="eyebrow-dot" /> Welcome to AnnaSetu</span>
            <h2 className="text-2xl sm:text-3xl font-serif text-[#173d2b] mt-2 mb-2 leading-tight">
              How would you like<br /><em>to make a difference?</em>
            </h2>
            <p className="text-xs text-stone-500 mb-6">
              Select your role in the food rescue network to sign in or register your organization.
            </p>

            <div className="modal-role-list space-y-3">
              {roles.map(({ id, label, description, icon: Icon }) => (
                <div
                  key={id}
                  className="flex items-center justify-between p-4 rounded-2xl border border-[#dce5d8] bg-white hover:border-[#8daa81] hover:shadow-md transition-all group cursor-pointer"
                  onClick={() => navigateToAuth(id)}
                >
                  <div className="flex items-center gap-3.5">
                    <span className="w-11 h-11 rounded-xl bg-[#e5efd5] text-[#173d2b] flex items-center justify-center group-hover:bg-[#173d2b] group-hover:text-amber-200 transition-colors shrink-0">
                      <Icon size={22} />
                    </span>
                    <div>
                      <strong className="block text-sm font-bold text-[#173d2b]">{label}</strong>
                      <small className="block text-xs text-stone-500 mt-0.5">{description}</small>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0 pl-2">
                    <span className="text-xs font-bold text-[#4f765c] group-hover:text-[#173d2b] transition-colors">
                      Enter
                    </span>
                    <ArrowRight size={16} className="text-[#87958b] group-hover:text-[#173d2b] group-hover:translate-x-1 transition-all" />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 pt-4 border-t border-[#e2ebd8] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-stone-500">
              <a
                href="#community"
                onClick={() => setShowRoles(false)}
                className="text-[#4f765c] hover:underline font-semibold flex items-center gap-1"
              >
                Browse community roles on page ↓
              </a>
              <button
                type="button"
                onClick={() => navigateToAuth()}
                className="text-stone-700 hover:text-[#173d2b] font-semibold cursor-pointer border-0 bg-transparent p-0"
              >
                All account sign in →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
