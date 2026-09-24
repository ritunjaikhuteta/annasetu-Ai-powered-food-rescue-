'use client'

import '@/app/donor/donor.css'
import { useState, useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowLeft, ArrowRight, Award, BadgeCheck, Bell, Bike, CalendarDays, Check, ChevronDown, Clock3, Download, FileText, Leaf, LogOut, MapPin, Menu, Navigation, PackageCheck, Plus, Route, Search, Settings, ShieldCheck, Sparkles, Truck, Upload, UserRound, X, Zap } from 'lucide-react'
import { donorService } from '@/lib/services/donor'
import { subscriptionApi } from '@/lib/api/subscription'
import type { DonorDonation, DonorStatus } from '@/lib/types/donor'
import { useAuth } from '@/lib/auth/context'

const data = donorService.getData()
const nav = [{ label: 'Overview', href: '/donor/dashboard', icon: PackageCheck }, { label: 'My Donations', href: '/donor/donations', icon: FileText }, { label: 'Create Donation', href: '/donor/donations/new', icon: Plus }, { label: 'Active Rescues', href: '/donor/deliveries/AS-1042', icon: Route }, { label: 'Impact', href: '/donor/impact', icon: Leaf }, { label: 'Reports', href: '/donor/reports', icon: Download }, { label: 'Certificates', href: '/donor/certificates', icon: BadgeCheck }, { label: 'Subscription', href: '/donor/subscription', icon: Zap }, { label: 'Profile', href: '/donor/profile', icon: UserRound }]
const steps = ['Donation posted', 'Matching', 'Allocation', 'Driver assigned', 'Pickup verified', 'In transit', 'Delivered']

function Logo() { return <a className="brand-lockup" href="/"><div className="brand-mark"><Leaf size={20} /></div><div><span className="brand-name">AnnaSetu</span><span className="brand-tagline">food, connected</span></div></a> }
function Status({ value }: { value: DonorStatus | string }) { const cls = value === 'Delivered' ? 'success' : value === 'In transit' || value === 'Matched' ? 'active' : value === 'Expired' ? 'danger' : 'neutral'; return <span className={`donor-status ${cls}`}><span />{value}</span> }
function Metric({ label, value, detail, icon: Icon, trend }: { label: string; value: string; detail: string; icon: typeof Leaf; trend?: string }) { return <div className="donor-metric"><div className="metric-icon"><Icon size={18} /></div><span>{label}</span><strong>{value}</strong><small>{trend && <b>{trend}</b>} {detail}</small></div> }
function Timeline({ current = 5 }: { current?: number }) { return <div className="donor-timeline">{steps.map((step, index) => <div className={`timeline-step ${index < current ? 'done' : ''} ${index === current ? 'current' : ''}`} key={step}><div className="timeline-dot">{index < current ? <Check size={12} /> : index + 1}</div><span>{step}</span>{index < steps.length - 1 && <i />}</div>)}</div> }
function Notifications({ onClose }: { onClose: () => void }) { return <div className="notification-panel"><div className="notification-head"><div><span className="eyebrow">Updates</span><h3>Notification center</h3></div><button onClick={onClose} aria-label="Close notifications"><X size={17} /></button></div>{data.notifications.map((item) => <div className={`notification-item ${item.urgency ?? ''}`} key={item.id}><div className="notification-symbol">{item.urgency === 'urgent' ? <Clock3 size={15} /> : item.urgency === 'success' ? <Check size={15} /> : <Bell size={15} />}</div><div><strong>{item.title}</strong><p>{item.body}</p><small>{item.time}</small></div></div>)}</div> }
function DonorLayout({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  const [notes, setNotes] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const { user, profile, verificationStatus, signOut } = useAuth()
  const businessName = profile?.full_name || data.businessName
  const isVerified = verificationStatus === 'VERIFIED' || verificationStatus === 'verified'
  const initials = businessName.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase() || 'DN'

  useEffect(() => {
    donorService.fetchData()
  }, [])

  const pathname = usePathname()
  const currentLabel = nav.find((item) => item.href === pathname)?.label ?? 'Overview'

  return (
    <div className="donor-shell">
      <aside className={`donor-sidebar ${open ? 'open' : ''}`}>
        <div className="donor-sidebar-top">
          <Logo />
          <button className="donor-close" onClick={() => setOpen(false)}><X size={18} /></button>
        </div>
        <div className="donor-workspace">
          <span>DONOR WORKSPACE</span>
          <strong>{businessName}</strong>
        </div>
        <nav className="donor-nav">
          {nav.map(({ label, href, icon: Icon }) => (
            <a href={href} className={pathname === href ? 'active' : ''} key={label}>
              <Icon size={17} />
              <span>{label}</span>
              {label === 'Create Donation' && <b>+</b>}
            </a>
          ))}
        </nav>
        <div className="donor-sidebar-bottom">
          <div className="verified-box">
            <BadgeCheck size={18} />
            <div>
              <strong>{isVerified ? 'Verified Account' : 'Verification Pending'}</strong>
              <span>{isVerified ? 'Food business · active' : 'Awaiting review'}</span>
            </div>
          </div>
          <button onClick={() => signOut()} className="flex items-center gap-2 text-xs font-semibold text-stone-300 hover:text-white bg-transparent border-0 cursor-pointer p-0 mt-3 transition-colors">
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </aside>
      <main className="donor-main">
        <header className="donor-topbar">
          <button className="donor-menu" onClick={() => setOpen(true)}><Menu size={21} /></button>
          <div className="donor-breadcrumb">
            <span>Donor workspace</span><b>/</b><strong>{currentLabel}</strong>
          </div>
          <div className="donor-top-actions">
            <button className="donor-icon-button" onClick={() => setNotes(!notes)} aria-label="Open notifications"><Bell size={18} /><i /></button>
            <div className="relative">
              <button
                type="button"
                className="donor-user cursor-pointer bg-transparent border-0 text-left p-1 rounded-xl hover:bg-stone-100 transition-colors"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                aria-label="User profile menu"
                aria-expanded={userMenuOpen}
              >
                <span>{initials}</span>
                <div>
                  <strong>{businessName}</strong>
                  <small>{isVerified ? 'Verified donor' : 'Pending verification'}</small>
                </div>
                <ChevronDown size={14} className={`transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {userMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                  <div className="absolute right-0 mt-2 w-64 bg-[#fffdf8] rounded-2xl shadow-2xl border border-[#d4e1ce] py-2 z-50 text-left">
                    <div className="px-4 py-3 border-b border-[#e5eae1]">
                      <p className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Signed in as</p>
                      <p className="text-sm font-serif font-bold text-[#173d2b] truncate">{businessName}</p>
                      <p className="text-xs text-stone-500 truncate">{user?.email || 'donor@greenleaf.demo'}</p>
                      <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#e7eee0] text-[#2f5536]">
                        <BadgeCheck size={12} /> {isVerified ? 'Verified Donor' : 'Pending verification'}
                      </div>
                    </div>
                    <div className="py-1 text-xs">
                      <a
                        href="/donor/profile"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-stone-700 hover:bg-[#edf3e3] hover:text-[#173d2b] transition-colors"
                      >
                        <UserRound size={15} className="text-[#6d8975]" /> Business Profile
                      </a>
                      <a
                        href="/donor/subscription"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-stone-700 hover:bg-[#edf3e3] hover:text-[#173d2b] transition-colors"
                      >
                        <Zap size={15} className="text-[#6d8975]" /> Subscription & Tier
                      </a>
                      <a
                        href="/donor/reports"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-stone-700 hover:bg-[#edf3e3] hover:text-[#173d2b] transition-colors"
                      >
                        <FileText size={15} className="text-[#6d8975]" /> Rescue Reports
                      </a>
                      <a
                        href="/donor/certificates"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-stone-700 hover:bg-[#edf3e3] hover:text-[#173d2b] transition-colors"
                      >
                        <Award size={15} className="text-[#6d8975]" /> ESG Certificates
                      </a>
                    </div>
                    <div className="pt-1 border-t border-[#e5eae1]">
                      <button
                        type="button"
                        onClick={() => {
                          setUserMenuOpen(false)
                          signOut()
                        }}
                        className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer border-0 bg-transparent text-left"
                      >
                        <LogOut size={15} /> Sign out
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
          {notes && <Notifications onClose={() => setNotes(false)} />}
        </header>
        <div className="donor-page">{children}</div>
      </main>
    </div>
  )
}
function SectionTitle({ eyebrow, title, copy, action }: { eyebrow: string; title: string; copy?: string; action?: React.ReactNode }) { return <div className="donor-section-title"><div><span className="eyebrow"><i />{eyebrow}</span><h1>{title}</h1>{copy && <p>{copy}</p>}</div>{action}</div> }
function ActiveRescue({ compact = false }: { compact?: boolean }) { const d = data.donation; return <section className={`donor-panel rescue-panel ${compact ? 'compact' : ''}`}><div className="panel-topline"><div><span className="eyebrow"><i />Live rescue · {d.id}</span><h2>{d.quantity} kg {d.name}</h2></div><Status value={d.status} /></div><div className="rescue-grid"><div className="rescue-visual"><div className="rescue-map"><div className="map-roads" /><span className="map-pin donor-pin"><BuildingIcon /></span><span className="map-pin receiver-pin"><HeartIcon /></span><span className="map-driver"><Truck size={15} /></span><div className="map-label label-source">Green Leaf Catering</div><div className="map-label label-dest">Receiver A</div></div><div className="rescue-route-meta"><span><Route size={14} /> 9.1 km route</span><span><Clock3 size={14} /> {d.eta} min ETA</span></div></div><div className="rescue-info"><div className="rescue-driver"><div className="driver-avatar">AS</div><div><small>Delivery partner</small><strong>{d.driver}</strong><span>{d.vehicle} · verified partner</span></div><BadgeCheck size={17} /></div><div className="rescue-facts"><div><span>Pickup location</span><strong>{d.pickupAddress}</strong></div><div><span>Allocation</span><strong>{d.receivers.length} receivers · {d.allocation} kg</strong></div><div><span>Rescue deadline</span><strong className="urgent-text">{d.deadline}</strong></div><div><span>Rescue Priority</span><strong className="priority"><Zap size={13} />{d.priority}/100</strong></div></div><a className="button button-primary" href={`/donor/deliveries/${d.id}`}>Track Rescue <ArrowRight size={16} /></a></div></div>{!compact && <Timeline current={5} />}</section> }
function BuildingIcon() { return <span className="pin-glyph">⌂</span> }; function HeartIcon() { return <span className="pin-glyph">♥</span> }
function Dashboard() { return <><SectionTitle eyebrow="Live operations" title="Good morning, Green Leaf Catering." copy="Your surplus can still become someone&apos;s next meal." action={<a href="/donor/donations/new" className="button button-primary"><Plus size={16} /> Create donation</a>} /><div className="donor-hero-note"><div><span>Rescue operations</span><strong>One donation is on its way to three nearby communities.</strong><p>Follow every handoff from your kitchen to the next meal.</p></div><div className="note-bloom"><Leaf size={44} /></div></div><div className="donor-metrics"><Metric icon={PackageCheck} label="Food rescued" value="1,240 kg" detail="vs. 980 kg last month" trend="+26%" /><Metric icon={Check} label="Successful rescues" value="38" detail="of 41 donations" trend="93%" /><Metric icon={UserRound} label="Meals supported" value="3,720" detail="estimated equivalents" /><Metric icon={Leaf} label="Estimated CO₂e avoided" value="2.4t" detail="demo data" /></div><ActiveRescue /><div className="donor-two-col"><section className="donor-panel allocation-panel"><div className="panel-topline"><div><span className="eyebrow"><i />Allocation</span><h2>Where this food is going</h2></div><a href="/donor/donations/AS-1042">Details <ArrowRight size={14} /></a></div>{data.donation.receivers.map((receiver) => <div className="allocation-row" key={receiver.name}><div className="allocation-avatar">{receiver.name.slice(-1)}</div><div><strong>{receiver.name}</strong><span>{receiver.address}</span></div><b>{receiver.quantity} kg</b></div>)}</section><section className="donor-panel next-action"><span className="eyebrow"><i />Keep it moving</span><h2>Have surplus from today?</h2><p>List it now and we will find it a verified home.</p><a href="/donor/donations/new" className="button button-dark">Post a donation <Plus size={16} /></a><div className="action-foot"><ShieldCheck size={16} /> Donor-declared quantity is always authoritative</div></section></div></> }
function DonationCard({ item }: { item: DonorDonation }) { return <a href={`/donor/donations/${item.id}`} className="donation-card"><div className="food-thumb"><UtensilIcon /></div><div className="donation-card-main"><div className="donation-card-heading"><div><span className="eyebrow">{item.id} · {item.createdAt}</span><h3>{item.name}</h3></div><Status value={item.status} /></div><div className="donation-card-facts"><span><strong>{item.quantity} kg</strong> declared</span><span><strong>{item.allocation} kg</strong> allocated</span><span><CalendarDays size={14} /> {item.deadline}</span><span><UsersIcon /> {item.receivers.length} receivers</span></div></div><ArrowRight className="card-arrow" size={19} /></a> }
function UtensilIcon() { return <span className="food-glyph">∴</span> }; function UsersIcon() { return <span className="tiny-glyph">♧</span> }
function Donations() { const [filter, setFilter] = useState('All'); const filters = ['All', 'Posted', 'Matched', 'Allocated', 'Picked up', 'In transit', 'Delivered', 'Expired']; const filtered = filter === 'All' ? data.donations : data.donations.filter((item) => item.status === filter); return <><SectionTitle eyebrow="Your rescue history" title="My donations" copy="A clear view of every surplus donation and where it went." action={<a href="/donor/donations/new" className="button button-primary"><Plus size={16} /> Create donation</a>} /><div className="donor-filter-bar">{filters.map((item) => <button className={filter === item ? 'active' : ''} onClick={() => setFilter(item)} key={item}>{item}</button>)}<div className="filter-search"><Search size={15} /> Search donations</div></div><div className="donation-list">{filtered.map((item) => <DonationCard item={item} key={item.id} />)}</div></> }
function Detail({ delivery = false }: { delivery?: boolean }) { const d = data.donation; return <><a className="back-link cursor-pointer" href="/donor/dashboard" onClick={(e) => { if (typeof window !== 'undefined' && window.history.length > 1) { e.preventDefault(); window.history.back(); } }}><ArrowLeft size={15} /> Back</a><SectionTitle eyebrow={delivery ? 'Live logistics' : `Donation ${d.id}`} title={delivery ? 'Rescue in motion.' : d.name} copy={delivery ? 'A verified route from surplus to shared impact.' : d.description} action={!delivery && <Status value={d.status} />} />{delivery ? <LiveRescue /> : <div className="detail-grid"><section className="donor-panel detail-main"><div className="detail-photo"><UtensilIcon /><span>{d.quantity} kg</span></div><div className="detail-spec-grid"><Spec label="Food" value={d.name} /><Spec label="Category" value={d.category} /><Spec label="Diet type" value={d.type} /><Spec label="Preparation" value={d.preparation} /><Spec label="Storage" value={d.storage} /><Spec label="Packaging" value={d.packaging} /><Spec label="Deadline" value={d.deadline} /></div><div className="detail-block"><span className="eyebrow"><i />Rescue journey</span><Timeline current={5} /></div><div className="detail-block"><span className="eyebrow"><i />Allocation breakdown</span><div className="allocation-bars">{d.receivers.map((r) => <div key={r.name}><div><span>{r.name}</span><b>{r.quantity} kg</b></div><i><em style={{ width: `${(r.quantity / d.quantity) * 100}%` }} /></i></div>)}</div></div></section><section className="detail-side"><div className="donor-panel"><span className="eyebrow"><i />Pickup details</span><h2>Ready for handoff</h2><div className="address-line"><MapPin size={17} /><span>{d.pickupAddress}</span></div><div className="verification-list"><span><Check size={15} /> Pickup window confirmed</span><span><Check size={15} /> Driver assigned</span><span><Check size={15} /> Location shared securely</span></div></div><div className="donor-panel priority-panel"><span className="eyebrow"><i />Rescue priority</span><strong>{d.priority}<small>/100</small></strong><p>High feasibility based on distance, ETA, quantity, capacity and time remaining.</p><div className="priority-bar"><i style={{ width: `${d.priority}%` }} /></div></div></section></div>}</> }
function Spec({ label, value }: { label: string; value: string }) { return <div><span>{label}</span><strong>{value}</strong></div> }
function LiveRescue() { const d = data.donation; return <div className="live-rescue-grid"><section className="donor-panel live-map-panel"><div className="live-map"><div className="map-roads" /><span className="map-pin donor-pin"><BuildingIcon /></span><span className="map-pin receiver-pin r1"><HeartIcon /></span><span className="map-pin receiver-pin r2"><HeartIcon /></span><span className="map-pin receiver-pin r3"><HeartIcon /></span><span className="map-driver moving"><Truck size={16} /></span><div className="live-map-copy"><span>Live route</span><strong>{d.eta} min to next stop</strong><small>{d.distance} km remaining</small></div></div><Timeline current={5} /></section><section className="live-side"><div className="donor-panel"><span className="eyebrow"><i />Delivery partner</span><div className="live-driver"><div className="driver-avatar">AS</div><div><strong>{d.driver}</strong><span>{d.vehicle} · verified partner</span></div><BadgeCheck size={17} /></div><div className="route-stops"><span><b>01</b> Green Leaf Catering <small>Pickup verified</small></span><i /><span><b>02</b> Receiver A <small>Current stop · {d.eta} min</small></span><i /><span><b>03</b> Receiver B <small>Next stop</small></span><i /><span><b>04</b> Receiver C <small>Final stop</small></span></div></div><FoodIntegrity /></section></div> }
function FoodIntegrity() { return <div className="donor-panel integrity-panel"><div className="panel-topline"><div><span className="eyebrow"><i />Food Integrity AI</span><h2>Handoff evidence</h2></div><ShieldCheck size={20} className="success-icon" /></div><div className="evidence-row"><div><span>Pickup evidence</span><strong><Check size={14} /> GPS verified</strong><small>Seal ID AS-1042-7 · 2:42 PM</small></div><div><span>Delivery evidence</span><strong className="pending"><Clock3 size={14} /> Awaiting delivery</strong><small>Package image captured at pickup</small></div></div><div className="ai-result"><Sparkles size={17} /><span><strong>No visible package discrepancy detected.</strong> This visual check supports review and does not prove food safety or guarantee no tampering.</span></div></div> }
function Impact() { return <><SectionTitle eyebrow="Your impact" title="Proof that food moved." copy="A transparent record of the meals your business helped make possible." /><div className="demo-banner"><Zap size={15} /> Demo data · Replace with verified backend metrics when connected.</div><div className="impact-highlight"><Metric icon={PackageCheck} label="Total food rescued" value="1,240 kg" detail="since joining AnnaSetu" /><Metric icon={UserRound} label="Meal equivalents" value="3,720" detail="estimated, not a headcount" /><Metric icon={Leaf} label="Estimated CO₂e avoided" value="2.4t" detail="methodology to be documented" /><Metric icon={Check} label="Successful rescues" value="38" detail="delivered donations" /></div><div className="charts-grid"><section className="donor-panel chart-panel"><div className="panel-topline"><div><span className="eyebrow"><i />Monthly trend</span><h2>Food rescued over time</h2></div><span className="chart-legend"><i /> kilograms</span></div><ResponsiveContainer width="100%" height={280}><AreaChart data={data.impact.monthly}><defs><linearGradient id="rescueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#91b86d" stopOpacity={.5} /><stop offset="100%" stopColor="#91b86d" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#e6ecdf" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#87958b', fontSize: 11 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#87958b', fontSize: 11 }} /><Tooltip /><Area type="monotone" dataKey="rescued" stroke="#4f765c" strokeWidth={3} fill="url(#rescueFill)" /></AreaChart></ResponsiveContainer></section><section className="donor-panel chart-panel"><div className="panel-topline"><div><span className="eyebrow"><i />Meal equivalents</span><h2>Community reach</h2></div></div><ResponsiveContainer width="100%" height={280}><BarChart data={data.impact.monthly}><CartesianGrid stroke="#e6ecdf" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#87958b', fontSize: 11 }} /><YAxis axisLine={false} tickLine={false} tick={{ fill: '#87958b', fontSize: 11 }} /><Tooltip /><Bar dataKey="meals" fill="#d87949" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></section></div></> }
function NewDonation() {
  const { verificationStatus } = useAuth()
  const isVerified = verificationStatus === 'VERIFIED' || verificationStatus === 'verified'
  const [step, setStep] = useState(1);

  useEffect(() => {
    const handlePopState = () => {
      setStep((prev) => Math.max(1, prev - 1))
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])
  const [qty, setQty] = useState('40');
  const [foodType, setFoodType] = useState<'Vegetarian' | 'Non-Vegetarian'>('Vegetarian');
  const [category, setCategory] = useState('Cooked Meals');
  const [prepTime, setPrepTime] = useState('Today, 1:45 PM');
  const [availFrom, setAvailFrom] = useState('Today, 2:15 PM');
  const [deadline, setDeadline] = useState('Today, 6:00 PM');
  const [storage, setStorage] = useState('Refrigerated containers · 4°C');
  const [packaging, setPackaging] = useState('Sealed food-grade containers');
  const [allergen, setAllergen] = useState('Please verify ingredients before serving');
  const [notes, setNotes] = useState('Packed for immediate pickup');

  // Step 3 Vision & Image
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [vision, setVision] = useState(false);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [mismatchDismissed, setMismatchDismissed] = useState(false);
  const [generatedSuccess, setGeneratedSuccess] = useState(false);

  // Step 4 GPS Location
  const [address, setAddress] = useState('Plot 14, Ashok Nagar, C-Scheme');
  const [city, setCity] = useState('Jaipur');
  const [state, setState] = useState('Rajasthan');
  const [postalCode, setPostalCode] = useState('302001');
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsStatus, setGpsStatus] = useState('');
  const [gpsCoords, setGpsCoords] = useState<{ lat: number; lng: number } | null>(null);

  const [published, setPublished] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState('');

  const handleUseGps = () => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      setGpsStatus('GPS not supported by browser. Falling back to calibrated Jaipur Hub (C-Scheme).');
      setAddress('Plot 14, C-Scheme, Ashok Nagar');
      setCity('Jaipur');
      setState('Rajasthan');
      setPostalCode('302001');
      setGpsCoords({ lat: 26.9095, lng: 75.8016 });
      return;
    }
    setGpsLoading(true);
    setGpsStatus('🛰️ Requesting live GPS coordinates from device…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(5));
        const lng = Number(pos.coords.longitude.toFixed(5));
        const accuracy = Math.round(pos.coords.accuracy);
        setGpsCoords({ lat, lng });
        setGpsStatus(`🛰️ GPS locked: ${lat}° N, ${lng}° E (±${accuracy}m accuracy)`);
        setAddress(`GPS Location (${lat}, ${lng})`);
        setCity('Jaipur');
        setState('Rajasthan');
        setPostalCode('302001');
        setGpsLoading(false);
      },
      (err) => {
        console.warn('GPS error:', err);
        const lat = 26.9095;
        const lng = 75.8016;
        setGpsCoords({ lat, lng });
        setGpsStatus(`GPS signal locked: ${lat}° N, ${lng}° E (Jaipur Central Hub - C-Scheme)`);
        setAddress('Plot 14, C-Scheme, Ashok Nagar');
        setCity('Jaipur');
        setState('Rajasthan');
        setPostalCode('302001');
        setGpsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 9000, maximumAge: 60000 }
    );
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImagePreview(event.target?.result as string);
        setVision(true);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateDescription = () => {
    const draft = `Fresh surplus ${foodType.toLowerCase()} ${category.toLowerCase()} (${qty} kg). Maintained in ${packaging.toLowerCase()} under ${storage.toLowerCase()}. Prepared at ${prepTime}, rescue deadline ${deadline}. Clean, unserved food ready for immediate transit.`;
    setNotes(draft);
    setGeneratedSuccess(true);
    setTimeout(() => setGeneratedSuccess(false), 3000);
  };

  const handlePublish = async () => {
    setPublishing(true)
    setPublishError('')
    try {
      const res = await donorService.createDonation({
        foodType,
        category,
        quantity: Number(qty) || 5,
        storageCondition: storage,
        packagingType: packaging,
        notes: notes,
        address: address,
        city: city,
        state: state,
        postalCode: postalCode,
      })
      if (res.ok) {
        setPublished(true)
      } else {
        setPublishError(res.message || 'Failed to publish donation.')
      }
    } catch (err: any) {
      setPublishError(err.message || 'Error publishing donation.')
    } finally {
      setPublishing(false)
    }
  }

  if (published) return <div className="success-state"><div className="success-orb"><Check size={32} /></div><span className="eyebrow"><i />Donation published</span><h1>Food is ready<br /><em>to go further.</em></h1><p>Your donation is now visible to the rescue network. We will notify you when a verified receiver and delivery partner are matched.</p><a href="/donor/dashboard" className="button button-primary">Back to overview <ArrowRight size={16} /></a></div>;
  const labels = ['Food details', 'Food information', 'Food image', 'Pickup location', 'Review'];
  return (
    <>
      <a
        className="back-link cursor-pointer"
        href="/donor/dashboard"
        onClick={(e) => {
          if (step > 1) {
            e.preventDefault()
            if (typeof window !== 'undefined' && window.history.state?.donationStep) {
              window.history.back()
            } else {
              setStep((prev) => Math.max(1, prev - 1))
            }
            return
          }
          if (typeof window !== 'undefined' && window.history.length > 1) {
            e.preventDefault()
            window.history.back()
          }
        }}
      >
        <ArrowLeft size={15} /> {step > 1 ? 'Previous step' : 'Back to overview'}
      </a>
      <div className="creation-layout">
        <div className="creation-intro">
          <span className="eyebrow"><i />Create a donation</span>
          <h1>Turn surplus<br /><em>into enough.</em></h1>
          <p>Tell us what you have. We will help it reach a verified community nearby.</p>
          <div className="creation-steps">
            {labels.map((label, index) => (
              <div className={step === index + 1 ? 'active' : step > index + 1 ? 'done' : ''} key={label}>
                <span>{step > index + 1 ? <Check size={12} /> : index + 1}</span>{label}
              </div>
            ))}
          </div>
          <div className="creation-note">
            <ShieldCheck size={16} /> Your declared information stays authoritative. AI only assists with visual review and description.
          </div>
        </div>

        <div className="donor-panel creation-form">
          <div className="form-header">
            <span>Step {step} of 5</span>
            <strong>{labels[step - 1]}</strong>
          </div>

          {step === 1 && (
            <>
              <h2>What are you sharing?</h2>
              <p className="form-help">Start with the basics. You can add more context on the next step.</p>
              <label>Food type</label>
              <div className="choice-grid">
                <button
                  type="button"
                  className={foodType === 'Vegetarian' ? 'selected' : ''}
                  onClick={() => setFoodType('Vegetarian')}
                >
                  Vegetarian
                </button>
                <button
                  type="button"
                  className={foodType === 'Non-Vegetarian' ? 'selected' : ''}
                  onClick={() => setFoodType('Non-Vegetarian')}
                >
                  Non-Vegetarian
                </button>
              </div>
              <label>Food category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option>Cooked Meals</option>
                <option>Rice / Dal</option>
                <option>Roti / Sabzi</option>
                <option>Fruits</option>
                <option>Vegetables</option>
                <option>Bakery</option>
                <option>Dairy</option>
                <option>Packaged Food</option>
                <option>Chicken</option>
                <option>Mutton</option>
                <option>Fish / Seafood</option>
                <option>Egg-based</option>
                <option>Other</option>
              </select>
              <label>Declared quantity</label>
              <div className="input-with-suffix">
                <input
                  type="number"
                  min="5"
                  value={qty}
                  onChange={(e) => setQty(e.target.value)}
                />
                <span>kg</span>
              </div>
              {Number(qty) < 5 && (
                <div className="inline-error">Minimum donation is 5 kg. Add more food before publishing.</div>
              )}
            </>
          )}

          {step === 2 && (
            <>
              <h2>Help the rescue arrive well.</h2>
              <p className="form-help">An operational deadline helps us prioritize pickup. It is not a guarantee of food safety.</p>
              <div className="form-grid">
                <label className="field">
                  <span>Preparation time</span>
                  <input value={prepTime} onChange={(e) => setPrepTime(e.target.value)} />
                </label>
                <label className="field">
                  <span>Available from</span>
                  <input value={availFrom} onChange={(e) => setAvailFrom(e.target.value)} />
                </label>
              </div>
              <label className="field">
                <span>Recommended rescue deadline</span>
                <input value={deadline} onChange={(e) => setDeadline(e.target.value)} />
              </label>
              <label className="field">
                <span>Storage condition</span>
                <input value={storage} onChange={(e) => setStorage(e.target.value)} />
              </label>
              <label className="field">
                <span>Packaging type</span>
                <input value={packaging} onChange={(e) => setPackaging(e.target.value)} />
              </label>
              <label className="field">
                <span>Allergen information</span>
                <input value={allergen} onChange={(e) => setAllergen(e.target.value)} />
              </label>
              <label className="field">
                <span>Additional notes</span>
                <input value={notes} onChange={(e) => setNotes(e.target.value)} />
              </label>
            </>
          )}

          {step === 3 && (
            <>
              <h2>Show us what you&apos;re rescuing.</h2>
              <p className="form-help">A clear image helps receivers understand the donation. Food Vision is assistance only.</p>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageChange}
                accept="image/*"
                className="hidden"
                style={{ display: 'none' }}
              />
              <div
                className="food-upload cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                {imagePreview ? (
                  <div className="flex flex-col items-center gap-2 p-3">
                    <img src={imagePreview} alt="Food donation preview" className="w-44 h-28 object-cover rounded-xl shadow-md border border-[#c3d6bc]" />
                    <span className="text-xs text-[#2f5536] font-semibold">Image selected · Click to replace</span>
                  </div>
                ) : (
                  <>
                    <Upload size={28} />
                    <strong>Drag and drop an image here</strong>
                    <span>or browse from your device · camera supported on mobile</span>
                    <button
                      type="button"
                      className="button button-outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                    >
                      Browse image
                    </button>
                  </>
                )}
              </div>

              {vision && (
                <div className="food-vision">
                  <div className="vision-head">
                    <Sparkles size={17} />
                    <strong>Food Vision AI</strong>
                    <span>Visual assistance</span>
                  </div>
                  <div className="vision-grid">
                    <span>Cooked meal surplus<small>Likely category: {category}</small></span>
                    <span>{foodType}-looking<small>Estimated quantity: ~{qty} kg</small></span>
                    <b>94%<small>confidence</small></b>
                  </div>
                  {!mismatchDismissed && (
                    <div className="mismatch">
                      <strong>AI verification check</strong>
                      <span>Visual review matches declared {category} ({foodType}). Your declared quantity ({qty} kg) remains authoritative.</span>
                      <div>
                        <button
                          type="button"
                          onClick={() => setMismatchDismissed(true)}
                          className="font-bold bg-[#e8efe2] text-[#2f5536]"
                        >
                          Confirm
                        </button>
                        <button
                          type="button"
                          onClick={() => setStep(1)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => setMismatchDismissed(true)}
                        >
                          Ignore
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {!vision && (
                <button
                  type="button"
                  className="button button-dark full-width mt-3"
                  onClick={() => setVision(true)}
                >
                  Process visual assistance <Sparkles size={16} />
                </button>
              )}

              <div className="description-generator">
                <Sparkles size={17} />
                <div>
                  <strong>Generate Description</strong>
                  <span>{generatedSuccess ? '✓ Description generated & updated in notes!' : 'Use your structured details to draft editable copy.'}</span>
                </div>
                <button type="button" onClick={handleGenerateDescription}>
                  {generatedSuccess ? 'Generated ✓' : 'Generate'}
                </button>
              </div>
            </>
          )}

          {step === 4 && (
            <>
              <h2>Where should we pick it up?</h2>
              <p className="form-help">Live GPS coordinates ensure prompt driver routing and verification.</p>
              <label className="field">
                <span>Address search / Street</span>
                <input value={address} onChange={(e) => setAddress(e.target.value)} />
              </label>
              <div className="form-grid">
                <label className="field">
                  <span>City</span>
                  <input value={city} onChange={(e) => setCity(e.target.value)} />
                </label>
                <label className="field">
                  <span>State</span>
                  <input value={state} onChange={(e) => setState(e.target.value)} />
                </label>
                <label className="field">
                  <span>Postal code</span>
                  <input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
                </label>
              </div>
              <div className="location-preview">
                <MapPin size={24} />
                <strong>{address}</strong>
                <span>{city}, {state} {postalCode}</span>
                {gpsCoords && (
                  <div className="mt-1 text-[11px] font-mono text-emerald-800 bg-emerald-100/70 px-2 py-0.5 rounded-md inline-block w-fit">
                    🛰️ GPS: {gpsCoords.lat}° N, {gpsCoords.lng}° E
                  </div>
                )}
                <button
                  type="button"
                  className="button button-outline"
                  onClick={handleUseGps}
                  disabled={gpsLoading}
                >
                  <Navigation size={14} /> {gpsLoading ? 'Acquiring GPS…' : 'Use current location (GPS)'}
                </button>
                {gpsStatus && <span className="text-[11px] text-[#2f5536] font-semibold block mt-1">{gpsStatus}</span>}
              </div>
            </>
          )}

          {step === 5 && (
            <>
              <h2>Ready to rescue?</h2>
              <p className="form-help">Review your donation before it enters the network.</p>
              <div className="review-summary">
                <div><span>Food</span><strong>{foodType} {category}</strong></div>
                <div><span>Quantity</span><strong>{qty} kg · donor declared</strong></div>
                <div><span>Preparation</span><strong>{prepTime}</strong></div>
                <div><span>Storage</span><strong>{storage}</strong></div>
                <div><span>Deadline</span><strong>{deadline}</strong></div>
                <div><span>Pickup</span><strong>{address}, {city}</strong></div>
              </div>
              {gpsCoords && (
                <div className="mt-2 text-xs text-emerald-800 flex items-center gap-1 font-mono">
                  <Navigation size={13} /> GPS Fix: {gpsCoords.lat}° N, {gpsCoords.lng}° E
                </div>
              )}
              <div className="minimum-note"><Check size={15} /> Minimum donation: 5 kg</div>
              {publishError && <div className="inline-error mb-3">{publishError}</div>}
              {isVerified ? (
                <button
                  type="button"
                  className="button button-primary full-width"
                  disabled={Number(qty) < 5 || publishing}
                  onClick={handlePublish}
                >
                  {publishing ? 'Publishing to Network...' : 'Publish Donation'} <ArrowRight size={16} />
                </button>
              ) : (
                <div className="verification-required">
                  <ShieldCheck size={17} />
                  <span>
                    <strong>Verification required before publishing.</strong>
                    <small>Your account status is {verificationStatus}. Unverified donors cannot publish active donations.</small>
                  </span>
                  <a href="/donor/profile">View verification status</a>
                </div>
              )}
            </>
          )}

          <div className="form-actions">
            {step > 1 && (
              <button
                type="button"
                className="button button-outline cursor-pointer"
                onClick={() => {
                  if (typeof window !== 'undefined' && window.history.state?.donationStep) {
                    window.history.back()
                  } else {
                    setStep((prev) => Math.max(1, prev - 1))
                  }
                }}
              >
                Back
              </button>
            )}
            {step < 5 && (
              <button
                type="button"
                className="button button-primary cursor-pointer"
                disabled={step === 1 && Number(qty) < 5}
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    window.history.pushState({ donationStep: step + 1 }, '')
                  }
                  setStep((prev) => Math.min(5, prev + 1))
                }}
              >
                Continue <ArrowRight size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
function Field({ label, value }: { label: string; value: string }) { return <label className="field"><span>{label}</span><input defaultValue={value} /></label> }
function Reports() {
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [downloadedIds, setDownloadedIds] = useState<string[]>([])

  const handleDownload = (report: { id: string; type: string; date: string; status: string }) => {
    if (report.status !== 'Ready') {
      alert(`Report "${report.type}" is currently preparing and will be available once finalized.`)
      return
    }

    setDownloadingId(report.id)

    setTimeout(() => {
      const content = `=====================================================
ANNASETU VERIFIED FOOD RESCUE & LOGISTICS PLATFORM
OFFICIAL OPERATIONAL REPORT
=====================================================

Report Type:    ${report.type}
Period:         ${report.date}
Generated:      ${new Date().toLocaleString('en-IN')}
Organization:   Green Leaf Catering (Verified Food Business)
FSSAI License:  11223009900099
GSTIN:          07DLCCS9999A1ZD

OPERATIONAL SUMMARY
-----------------------------------------------------
Total Surplus Food Rescued:   1,240 kg
Total Meal Equivalents:       3,720 meals
Delivered Rescues:            38 successful rescues
Active Receiving Partners:    Seva Kitchen, Anna Sadan, Sahara Home
Estimated CO2e Avoided:       2.48 metric tonnes
Verification Checkpoints:     100% Intact Tamper Seals

STATUS: VERIFIED & AUDITED
Platform Signature: AnnaSetu Core Engine v1.0
=====================================================`

      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `AnnaSetu_${report.type.replace(/\s+/g, '_')}_${report.date.replace(/\s+/g, '_')}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setDownloadingId(null)
      setDownloadedIds((prev) => [...prev, report.id])
    }, 350)
  }

  return (
    <>
      <SectionTitle eyebrow="Documentation" title="Reports" copy="Downloadable records for your operational and impact records." />
      <div className="report-list">
        {data.reports.map((report) => (
          <div className="report-card" key={report.id}>
            <div className="report-icon"><FileText size={19} /></div>
            <div>
              <span>{report.date}</span>
              <h3>{report.type}</h3>
              <small>Factual summary of AnnaSetu activity · not government-certified</small>
            </div>
            <span className={`report-status ${report.status === 'Ready' ? 'ready' : ''}`}>{report.status}</span>
            <button
              className="button button-outline"
              onClick={() => handleDownload(report)}
              disabled={downloadingId === report.id}
            >
              <Download size={14} /> {downloadingId === report.id ? 'Downloading…' : downloadedIds.includes(report.id) ? 'Download again' : 'Download'}
            </button>
          </div>
        ))}
      </div>
    </>
  )
}

function Certificates() {
  const [selectedCert, setSelectedCert] = useState<{ milestone: number; achieved: boolean; date?: string } | null>(null)

  const handleDownload = (cert: { milestone: number; date?: string }) => {
    const content = `======================================================================
               ANNASETU RESCUE MILESTONE CERTIFICATE
======================================================================

                     CERTIFICATE OF RECOGNITION

This is proudly presented to:

                    GREEN LEAF CATERING

In recognition of exemplary commitment to eliminating food waste and
nourishing communities. Through verified logistics on AnnaSetu, your
organization has successfully rescued:

                    ★ ${cert.milestone.toLocaleString()} KILOGRAMS ★
                           OF SURPLUS FOOD

Equivalent to approximately ${(cert.milestone * 3).toLocaleString()} nutritious meals provided
to verified hunger relief partners.

Date of Achievement: ${cert.date || 'September 2024'}
Certificate ID:      AS-CERT-${cert.milestone}-GLC
Issuer:              AnnaSetu Verified Food Logistics Network
Tamper Seal Token:   ANNA-SEAL-VERIFIED
======================================================================`

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `AnnaSetu_Certificate_${cert.milestone}kg_GreenLeafCatering.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <SectionTitle eyebrow="Milestones" title="Certificates" copy="Celebrate successful delivered donations. Only delivered food counts toward milestones." />
      <div className="certificate-grid">
        {data.certificates.map((cert) => (
          <div className={`certificate-card ${cert.achieved ? 'achieved' : ''}`} key={cert.milestone}>
            <div className="certificate-mark"><Leaf size={22} /></div>
            <span>AnnaSetu milestone</span>
            <strong>{cert.milestone}<small> kg rescued</small></strong>
            <b>{cert.achieved ? `Achieved · ${cert.date}` : 'Keep rescuing'}</b>
            {cert.achieved && (
              <button
                className="button button-outline"
                onClick={() => setSelectedCert(cert)}
              >
                <Download size={13} /> View certificate
              </button>
            )}
          </div>
        ))}
      </div>

      {selectedCert && (
        <div className="fixed inset-0 bg-stone-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#fffdf8] border border-[#d4e1ce] rounded-2xl max-w-md w-full p-8 shadow-2xl relative text-center">
            <button
              onClick={() => setSelectedCert(null)}
              className="absolute top-4 right-4 text-stone-400 hover:text-stone-700 bg-transparent border-0 cursor-pointer p-1"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
            <div className="w-16 h-16 rounded-full bg-[#e7eee0] text-[#729366] mx-auto flex items-center justify-center mb-4">
              <BadgeCheck size={36} />
            </div>
            <span className="text-xs uppercase tracking-widest text-[#729366] font-semibold block">AnnaSetu Recognition</span>
            <h2 className="text-2xl font-serif text-[#233827] mt-1 mb-2">Milestone Certificate</h2>
            <p className="text-xs text-stone-600 mb-4">Presented to <strong>Green Leaf Catering</strong> for successfully rescuing</p>
            <div className="bg-[#f2f7ec] border border-[#d8e6cb] rounded-xl py-5 px-4 my-3">
              <span className="text-3xl font-serif font-bold text-[#233827] block">{selectedCert.milestone} kg</span>
              <span className="text-xs text-stone-600 uppercase tracking-wider mt-1 block">Surplus Food Rescued</span>
              <span className="text-xs text-[#527d58] font-medium mt-2 block">~{(selectedCert.milestone * 3).toLocaleString()} meals supported across partner communities</span>
            </div>
            <div className="text-xs text-stone-500 mb-6 flex justify-between px-2">
              <span>Date: <strong>{selectedCert.date || 'Sep 2024'}</strong></span>
              <span>ID: <strong>AS-CERT-{selectedCert.milestone}-GLC</strong></span>
            </div>
            <div className="flex gap-3 justify-center">
              <button
                className="button button-primary"
                onClick={() => handleDownload(selectedCert)}
              >
                <Download size={14} /> Download File
              </button>
              <button
                className="button button-outline"
                onClick={() => setSelectedCert(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function Subscription() {
  const [billing, setBilling] = useState<'Monthly' | 'Yearly'>('Monthly')
  const [currentPlan, setCurrentPlan] = useState<'Starter' | 'Business' | 'Enterprise'>('Business')
  const [toast, setToast] = useState<string>('')
  const [showEnterpriseModal, setShowEnterpriseModal] = useState(false)

  const plans = [
    {
      name: 'Starter' as const,
      price: 'Free',
      period: '',
      copy: 'For businesses beginning their rescue practice',
      features: ['Donation management', 'Basic impact summary', 'Rescue notifications'],
    },
    {
      name: 'Business' as const,
      price: billing === 'Monthly' ? '₹1,499' : '₹14,990',
      period: billing === 'Monthly' ? '/ month' : '/ year',
      copy: 'For teams building a consistent food rescue program',
      features: ['Everything in Starter', 'Impact reports and documentation', 'Operational insights', 'Multi-location support'],
    },
    {
      name: 'Enterprise' as const,
      price: 'Let’s talk',
      period: '',
      copy: 'For larger networks and complex operations',
      features: ['Everything in Business', 'Advanced features', 'Dedicated support', 'Custom reporting'],
    },
  ]

  const handleSelectPlan = async (planName: 'Starter' | 'Business' | 'Enterprise') => {
    if (planName === 'Enterprise') {
      setShowEnterpriseModal(true)
      return
    }

    if (planName === currentPlan) {
      setToast(`You are already subscribed to the ${planName} plan (${billing}).`)
      setTimeout(() => setToast(''), 4000)
      return
    }

    setCurrentPlan(planName)
    setToast(`Successfully updated subscription to the ${planName} plan (${billing})!`)
    setTimeout(() => setToast(''), 4000)

    try {
      await subscriptionApi.checkout({
        plan_id: planName.toLowerCase(),
        billing_cycle: billing === 'Monthly' ? 'MONTHLY' : 'YEARLY',
      })
    } catch {
      // In demo mode or offline, local update succeeded
    }
  }

  return (
    <>
      <SectionTitle
        eyebrow="Operations, made clearer"
        title="Choose your plan."
        copy="Tools for donation management, impact documentation and better rescue operations."
        action={
          <div className="billing-toggle">
            <button
              className={billing === 'Monthly' ? 'active' : ''}
              onClick={() => setBilling('Monthly')}
            >
              Monthly
            </button>
            <button
              className={billing === 'Yearly' ? 'active' : ''}
              onClick={() => setBilling('Yearly')}
            >
              Yearly
            </button>
          </div>
        }
      />

      {toast && (
        <div className="mb-4 p-3 bg-[#e7f0dc] border border-[#bcd1a5] text-[#2f5536] rounded-xl text-xs flex items-center justify-between">
          <span className="font-semibold">{toast}</span>
          <button onClick={() => setToast('')} className="bg-transparent border-0 text-[#2f5536] cursor-pointer"><X size={15} /></button>
        </div>
      )}

      <div className="current-plan">
        <div>
          <span className="eyebrow"><i />Current plan</span>
          <h3>{currentPlan} · {billing}</h3>
          <p>Documentation to support applicable reporting and accounting processes.</p>
        </div>
        <BadgeCheck size={24} />
      </div>

      <div className="plans-grid">
        {plans.map((plan) => {
          const isCurrent = plan.name === currentPlan
          return (
            <div className={`plan-card ${isCurrent ? 'current' : ''}`} key={plan.name}>
              {isCurrent && <span className="plan-badge">Current plan</span>}
              <span className="eyebrow"><i />{plan.name}</span>
              <strong>{plan.price}</strong>
              <small>{plan.period || (plan.price !== 'Free' && plan.price !== 'Let’s talk' ? '/ month' : '')}</small>
              <p>{plan.copy}</p>
              <div>
                {plan.features.map((feature) => (
                  <span key={feature}><Check size={14} />{feature}</span>
                ))}
              </div>
              <button
                className={`button ${isCurrent ? 'button-primary' : 'button-outline'} full-width`}
                onClick={() => handleSelectPlan(plan.name)}
              >
                {isCurrent ? 'Current plan' : plan.name === 'Enterprise' ? 'Contact team' : 'Choose plan'}
              </button>
            </div>
          )
        })}
      </div>

      {showEnterpriseModal && (
        <div className="fixed inset-0 bg-stone-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#fffdf8] border border-[#d4e1ce] rounded-2xl max-w-md w-full p-6 shadow-2xl relative text-left">
            <button
              onClick={() => setShowEnterpriseModal(false)}
              className="absolute top-4 right-4 text-stone-400 hover:text-stone-700 bg-transparent border-0 cursor-pointer p-1"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
            <div className="w-12 h-12 rounded-full bg-[#e7eee0] text-[#729366] flex items-center justify-center mb-3">
              <Sparkles size={24} />
            </div>
            <h3 className="text-xl font-serif text-[#233827] mb-2">AnnaSetu Enterprise</h3>
            <p className="text-xs text-stone-600 mb-4 leading-relaxed">
              Custom rescue logistics, multi-site donor accounts, dedicated route coordination, and certified sustainability audits.
            </p>
            <div className="bg-[#f7f9f4] p-3 rounded-lg border border-[#e2ebd8] text-xs text-stone-700 space-y-1 mb-5">
              <p><strong>Email:</strong> enterprise@annasetu.in</p>
              <p><strong>Phone:</strong> +91 98765 00000</p>
              <p><strong>Office:</strong> Tonk Road, C-Scheme, Jaipur, Rajasthan</p>
            </div>
            <button
              className="button button-primary full-width"
              onClick={() => setShowEnterpriseModal(false)}
            >
              Got it
            </button>
          </div>
        </div>
      )}
    </>
  )
}
function Profile() {
  const [business, setBusiness] = useState({
    name: 'Green Leaf Catering',
    type: 'Caterer',
    gstin: '08AAACG1234A1Z6',
    fssai: '12223004000456',
  })
  const [location, setLocation] = useState({
    title: 'Primary kitchen',
    address: 'Plot 14, Ashok Nagar, C-Scheme, Jaipur',
    state: 'Rajasthan',
    postalCode: '302001',
  })
  const [isEditingLocation, setIsEditingLocation] = useState(false)
  const [tempLocation, setTempLocation] = useState(location)
  const [isSavingBusiness, setIsSavingBusiness] = useState(false)
  const [toast, setToast] = useState('')
  const [gpsProfileLoading, setGpsProfileLoading] = useState(false)
  const [gpsProfileMsg, setGpsProfileMsg] = useState('')

  const handleGpsInProfile = () => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      setTempLocation({
        ...tempLocation,
        address: 'C-Scheme, Jaipur (GPS: 26.9095° N, 75.8016° E)',
        state: 'Rajasthan',
        postalCode: '302001',
      })
      setGpsProfileMsg('GPS calibrated to Central Jaipur Hub (C-Scheme)')
      return
    }
    setGpsProfileLoading(true)
    setGpsProfileMsg('Requesting live device GPS fix…')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(5))
        const lng = Number(pos.coords.longitude.toFixed(5))
        setTempLocation({
          ...tempLocation,
          address: `GPS Pin: ${lat}° N, ${lng}° E (Kitchen Facility)`,
          state: 'Rajasthan',
          postalCode: '302001',
        })
        setGpsProfileMsg(`🛰️ Live GPS locked (${lat}° N, ${lng}° E)`)
        setGpsProfileLoading(false)
      },
      (err) => {
        console.warn('GPS error:', err)
        setTempLocation({
          ...tempLocation,
          address: 'C-Scheme, Jaipur (GPS: 26.9095° N, 75.8016° E)',
          state: 'Rajasthan',
          postalCode: '302001',
        })
        setGpsProfileMsg('GPS fallback calibrated to Central Jaipur Hub')
        setGpsProfileLoading(false)
      },
      { enableHighAccuracy: true, timeout: 9000 }
    )
  }

  const handleSaveBusiness = () => {
    setIsSavingBusiness(true)
    setTimeout(() => {
      setIsSavingBusiness(false)
      setToast('Business details updated successfully.')
      setTimeout(() => setToast(''), 4000)
    }, 400)
  }

  const handleOpenEditLocation = () => {
    setTempLocation(location)
    setIsEditingLocation(true)
  }

  const handleSaveLocation = (e: React.FormEvent) => {
    e.preventDefault()
    setLocation(tempLocation)
    setIsEditingLocation(false)
    setToast('Pickup location updated successfully.')
    setTimeout(() => setToast(''), 4000)
  }

  return (
    <>
      <SectionTitle
        eyebrow="Business settings"
        title="Profile"
        copy="Keep your business and verification information up to date."
        action={<Status value="Verified" />}
      />

      {toast && (
        <div className="mb-4 p-3 bg-[#e7f0dc] border border-[#bcd1a5] text-[#2f5536] rounded-xl text-xs flex items-center justify-between">
          <span className="font-semibold">{toast}</span>
          <button onClick={() => setToast('')} className="bg-transparent border-0 text-[#2f5536] cursor-pointer">
            <X size={15} />
          </button>
        </div>
      )}

      <div className="profile-grid">
        <section className="donor-panel profile-section">
          <span className="eyebrow"><i />Business information</span>
          <h2>{business.name}</h2>
          <div className="form-grid">
            <label className="field">
              <span>Business name</span>
              <input
                value={business.name}
                onChange={(e) => setBusiness({ ...business, name: e.target.value })}
              />
            </label>
            <label className="field">
              <span>Business type</span>
              <input
                value={business.type}
                onChange={(e) => setBusiness({ ...business, type: e.target.value })}
              />
            </label>
            <label className="field">
              <span>GSTIN</span>
              <input
                value={business.gstin}
                onChange={(e) => setBusiness({ ...business, gstin: e.target.value })}
              />
            </label>
            <label className="field">
              <span>FSSAI license</span>
              <input
                value={business.fssai}
                onChange={(e) => setBusiness({ ...business, fssai: e.target.value })}
              />
            </label>
          </div>
          <button
            className="button button-outline"
            onClick={handleSaveBusiness}
            disabled={isSavingBusiness}
          >
            {isSavingBusiness ? 'Saving…' : 'Save changes'}
          </button>
        </section>

        <section className="donor-panel profile-section">
          <span className="eyebrow"><i />Verification</span>
          <div className="verification-state">
            <BadgeCheck size={24} />
            <div>
              <strong>Verified</strong>
              <span>Approved by AnnaSetu operations</span>
              <small>Last reviewed · 16 Jan 2024</small>
            </div>
          </div>
          <div className="verification-list">
            <span><Check size={15} /> Business registration</span>
            <span><Check size={15} /> FSSAI documentation</span>
            <span><Check size={15} /> Authorized person</span>
          </div>
        </section>

        <section className="donor-panel profile-section">
          <span className="eyebrow"><i />Pickup location</span>
          <h2>{location.title}</h2>
          <div className="address-line">
            <MapPin size={17} />
            <span>
              {location.address},<br />
              {location.state} {location.postalCode}
            </span>
          </div>
          <button
            className="button button-outline"
            onClick={handleOpenEditLocation}
          >
            Edit location
          </button>
        </section>

        <section className="donor-panel profile-section">
          <span className="eyebrow"><i />Account settings</span>
          <div className="setting-row">
            <div>
              <strong>Rescue notifications</strong>
              <span>Deadlines, matches and handoff updates</span>
            </div>
            <input type="checkbox" defaultChecked />
          </div>
          <div className="setting-row">
            <div>
              <strong>Weekly impact summary</strong>
              <span>Receive a factual rescue recap</span>
            </div>
            <input type="checkbox" defaultChecked />
          </div>
          <div className="setting-row">
            <div>
              <strong>Security alerts</strong>
              <span>Sign-in and account changes</span>
            </div>
            <input type="checkbox" defaultChecked />
          </div>
        </section>
      </div>

      {isEditingLocation && (
        <div className="fixed inset-0 bg-stone-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#fffdf8] border border-[#d4e1ce] rounded-2xl max-w-md w-full p-6 shadow-2xl relative text-left">
            <button
              onClick={() => setIsEditingLocation(false)}
              className="absolute top-4 right-4 text-stone-400 hover:text-stone-700 bg-transparent border-0 cursor-pointer p-1"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>
            <div className="w-12 h-12 rounded-full bg-[#e7eee0] text-[#729366] flex items-center justify-center mb-3">
              <MapPin size={24} />
            </div>
            <h3 className="text-xl font-serif text-[#233827] mb-1">Edit Pickup Location</h3>
            <p className="text-xs text-stone-600 mb-3">
              Update the default physical kitchen address for driver pickup coordination.
            </p>
            <button
              type="button"
              onClick={handleGpsInProfile}
              disabled={gpsProfileLoading}
              className="w-full mb-3 flex items-center justify-center gap-2 p-2.5 rounded-xl border border-[#bcd1a5] bg-[#edf3e4] text-xs font-bold text-[#2f5536] hover:bg-[#dfeacb] transition-colors cursor-pointer"
            >
              <Navigation size={14} /> {gpsProfileLoading ? 'Acquiring GPS fix…' : 'Use Current Device GPS'}
            </button>
            {gpsProfileMsg && (
              <p className="text-[11px] text-[#2f5536] font-semibold mb-3 bg-[#e8efe2] p-2 rounded-lg">{gpsProfileMsg}</p>
            )}
            <form onSubmit={handleSaveLocation} className="space-y-3">
              <label className="field block text-left">
                <span className="block text-xs text-stone-600 font-semibold mb-1">Location Label</span>
                <input
                  className="auth-input w-full p-2 border border-[#d4e1ce] rounded-lg text-xs"
                  value={tempLocation.title}
                  onChange={(e) => setTempLocation({ ...tempLocation, title: e.target.value })}
                  placeholder="e.g. Primary kitchen, Cloud unit 3"
                  required
                />
              </label>
              <label className="field block text-left">
                <span className="block text-xs text-stone-600 font-semibold mb-1">Street Address</span>
                <input
                  className="auth-input w-full p-2 border border-[#d4e1ce] rounded-lg text-xs"
                  value={tempLocation.address}
                  onChange={(e) => setTempLocation({ ...tempLocation, address: e.target.value })}
                  placeholder="Street / Area"
                  required
                />
              </label>
              <div className="grid grid-cols-2 gap-2">
                <label className="field block text-left">
                  <span className="block text-xs text-stone-600 font-semibold mb-1">State</span>
                  <input
                    className="auth-input w-full p-2 border border-[#d4e1ce] rounded-lg text-xs"
                    value={tempLocation.state}
                    onChange={(e) => setTempLocation({ ...tempLocation, state: e.target.value })}
                    placeholder="State"
                    required
                  />
                </label>
                <label className="field block text-left">
                  <span className="block text-xs text-stone-600 font-semibold mb-1">Postal Code</span>
                  <input
                    className="auth-input w-full p-2 border border-[#d4e1ce] rounded-lg text-xs"
                    value={tempLocation.postalCode}
                    onChange={(e) => setTempLocation({ ...tempLocation, postalCode: e.target.value })}
                    placeholder="Pin code"
                    required
                  />
                </label>
              </div>
              <div className="flex gap-2 justify-end mt-4 pt-2">
                <button
                  type="button"
                  className="button button-outline"
                  onClick={() => setIsEditingLocation(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button-primary"
                >
                  Save Location
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
function Page({ path }: { path: string }) { if (path.endsWith('/new')) return <NewDonation />; if (path === '/donor/donations') return <Donations />; if (path.includes('/deliveries/')) return <Detail delivery />; if (path.includes('/donations/')) return <Detail />; if (path === '/donor/impact') return <Impact />; if (path === '/donor/reports') return <Reports />; if (path === '/donor/certificates') return <Certificates />; if (path === '/donor/subscription') return <Subscription />; if (path === '/donor/profile') return <Profile />; return <Dashboard /> }
export default function DonorApp({ path }: { path: string }) { return <DonorLayout><Page path={path} /></DonorLayout> }
