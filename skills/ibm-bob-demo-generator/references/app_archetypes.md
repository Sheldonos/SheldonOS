# IBM Bob Demo — App Archetype Library

This library contains 8 pre-validated app archetypes for the WOW-First demo framework. Each archetype includes the Reddit signal source, the Master Prompt for IBM Project Bob, the PostgreSQL schema starter, and the WOW moment description.

---

## Archetype 1: The Micro-Landlord Portal

**Reddit Signal:** *"I have 3 rental units. I manage maintenance requests via text messages and a Google Sheet. Every property management app I've tried starts at $100/month and is built for companies with 50+ units. I'm using texts and prayer."* — r/Entrepreneur

**Target User:** Independent landlords with 1–5 rental units.

**The WOW Moment:** A tenant submits a maintenance request with a photo from their phone. The landlord sees it instantly on a clean dashboard, assigns it to a contractor with one click, and the tenant gets an automatic status update. No texts. No spreadsheets.

**Master Prompt for IBM Project Bob:**
```
Build a Micro-Landlord Portal for independent landlords with 1-5 rental units.

Problem: Small landlords manage maintenance requests via text messages and spreadsheets. 
Enterprise property management software starts at $100+/month and is built for companies 
with 50+ units. Small landlords need a simple, affordable alternative.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Properties: id, landlord_id, address, unit_count, created_at
- Tenants: id, property_id, name, email, phone, lease_start, lease_end, created_at
- MaintenanceTickets: id, tenant_id, property_id, title, description, photo_url, 
  status (ENUM: open, assigned, in_progress, resolved), priority, contractor_id, 
  created_at, resolved_at
- Contractors: id, landlord_id, name, email, phone, specialty, created_at

Core Features:
1. Tenant-facing request submission form (no login required, link-based access)
2. Landlord dashboard showing all open tickets sorted by priority and age
3. One-click contractor assignment with automatic email notification
4. Status history log for each ticket (audit trail)
5. JWT-based landlord authentication

UI Requirements:
- Dashboard as home screen with ticket count cards by status
- Ticket detail view with photo preview and status timeline
- Mobile-responsive for landlords checking on the go

The application must include input validation, structured JSON logging, and a 
read-only tenant status page accessible via a unique ticket URL.
```

**PostgreSQL Schema Starter:**
```sql
CREATE TYPE ticket_status AS ENUM ('open', 'assigned', 'in_progress', 'resolved');
CREATE TYPE ticket_priority AS ENUM ('low', 'medium', 'high', 'emergency');

CREATE TABLE landlords (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE properties (
  id SERIAL PRIMARY KEY,
  landlord_id INTEGER REFERENCES landlords(id) ON DELETE CASCADE,
  address TEXT NOT NULL,
  unit_count INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tenants (
  id SERIAL PRIMARY KEY,
  property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  lease_start DATE,
  lease_end DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE contractors (
  id SERIAL PRIMARY KEY,
  landlord_id INTEGER REFERENCES landlords(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  phone VARCHAR(20),
  specialty VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE maintenance_tickets (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER REFERENCES tenants(id),
  property_id INTEGER REFERENCES properties(id),
  contractor_id INTEGER REFERENCES contractors(id),
  title VARCHAR(255) NOT NULL,
  description TEXT,
  photo_url TEXT,
  status ticket_status DEFAULT 'open',
  priority ticket_priority DEFAULT 'medium',
  public_token VARCHAR(64) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP
);

CREATE INDEX idx_tickets_status ON maintenance_tickets(status);
CREATE INDEX idx_tickets_property ON maintenance_tickets(property_id);
```

---

## Archetype 2: The Tradesperson Scheduler

**Reddit Signal:** *"I'm a plumber. Every scheduling tool I've tried is built for office workers. I need to block out drive time between jobs, see which part of town I'm in each day, and let customers book available slots. Calendly doesn't understand that I can't go from the north side to the south side in 20 minutes."* — r/smallbusiness

**Target User:** Independent plumbers, electricians, HVAC technicians, and other field service workers.

**The WOW Moment:** A customer visits the plumber's booking page, sees only time slots that are geographically feasible based on the plumber's existing jobs that day, and books a slot. The plumber's daily view shows a route-optimized schedule with drive time blocks already accounted for.

**Master Prompt for IBM Project Bob:**
```
Build a Tradesperson Scheduler for independent field service workers (plumbers, electricians, HVAC).

Problem: Existing scheduling tools are built for office workers. Field service workers 
need to account for drive time between jobs, geographic clustering of appointments, 
and customer self-booking that respects these constraints.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Tradespeople: id, name, email, phone, trade_type, service_radius_miles, created_at
- ServiceZones: id, tradesperson_id, zone_name, zip_codes (array), created_at
- Jobs: id, tradesperson_id, customer_name, customer_email, customer_phone, 
  address, zip_code, job_type, start_time, end_time, drive_time_minutes, 
  status (ENUM: scheduled, in_progress, completed, cancelled), notes, created_at
- Availability: id, tradesperson_id, day_of_week, start_time, end_time, 
  is_available BOOLEAN

Core Features:
1. Daily calendar view showing jobs with drive time blocks between them
2. Customer-facing booking page showing only geographically feasible time slots
3. Automatic drive time buffer calculation based on job zip codes
4. Zone-based day planning (e.g., "Mondays I stay on the north side")
5. SMS confirmation to customer on booking

UI Requirements:
- Timeline-style daily view as the primary interface
- Color-coded jobs by type (new install, repair, emergency)
- Customer booking page must work on mobile without login

The application must include timezone-aware scheduling and prevent double-booking.
```

**PostgreSQL Schema Starter:**
```sql
CREATE TYPE job_status AS ENUM ('scheduled', 'in_progress', 'completed', 'cancelled');

CREATE TABLE tradespeople (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  trade_type VARCHAR(100),
  service_radius_miles INTEGER DEFAULT 25,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE service_zones (
  id SERIAL PRIMARY KEY,
  tradesperson_id INTEGER REFERENCES tradespeople(id) ON DELETE CASCADE,
  zone_name VARCHAR(100) NOT NULL,
  zip_codes TEXT[] NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  tradesperson_id INTEGER REFERENCES tradespeople(id) ON DELETE CASCADE,
  customer_name VARCHAR(255) NOT NULL,
  customer_email VARCHAR(255),
  customer_phone VARCHAR(20),
  address TEXT NOT NULL,
  zip_code VARCHAR(10),
  job_type VARCHAR(100),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  drive_time_minutes INTEGER DEFAULT 0,
  status job_status DEFAULT 'scheduled',
  notes TEXT,
  booking_token VARCHAR(64) UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_tradesperson_date ON jobs(tradesperson_id, start_time);
CREATE INDEX idx_jobs_status ON jobs(status);
```

---

## Archetype 3: The SaaS Price Sentinel

**Reddit Signal:** *"I just got charged $40 more than last month by a SaaS tool I use. They raised prices during my introductory period and I had no idea. I found 2 tools that do this but both require me to manually enter every subscription. I want something that detects it automatically."* — r/AppIdeas (184 upvotes)

**Target User:** Startup operators, SMB finance teams, and individual power users with multiple SaaS subscriptions.

**The WOW Moment:** The dashboard shows a timeline of every subscription price change detected in the past 6 months, with a red alert badge on any subscription that raised its price since the user signed up. One click shows the price history chart and the exact date of each change.

**Master Prompt for IBM Project Bob:**
```
Build a SaaS Price Sentinel for startup operators and SMB finance teams.

Problem: SaaS tools silently raise prices after introductory periods. Users have no 
automated way to detect these changes before they are charged. Existing tools require 
manual entry of every subscription.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Users: id, email, password_hash, created_at
- Subscriptions: id, user_id, service_name, service_url, current_price, 
  currency, billing_cycle (ENUM: monthly, annual), signup_price, 
  signup_date, last_checked_at, created_at
- PriceHistory: id, subscription_id, price, detected_at, change_amount, 
  change_percentage, is_increase BOOLEAN
- Alerts: id, user_id, subscription_id, alert_type, message, is_read BOOLEAN, 
  created_at

Core Features:
1. Dashboard showing all subscriptions with price change indicators
2. Price history chart for each subscription (line chart, price over time)
3. Alert feed showing all detected price increases, sorted by impact ($ amount)
4. Manual subscription entry with automatic price monitoring via scheduled checks
5. Email digest of weekly price change summary

UI Requirements:
- Summary cards at the top: total monthly spend, number of price increases this month
- Subscription list with color-coded change indicators (green = stable, red = increased)
- Alert badge on the nav for unread price change notifications

The application must include a background job scheduler for periodic price checks 
and structured audit logging of all price change detections.
```

---

## Archetype 4: The Field Inspection Logger

**Reddit Signal:** *"Our site supervisors do safety inspections on paper forms, take photos on their phones, and then someone has to manually enter everything into a spreadsheet. We have no searchable history of findings, no way to track remediation, and no audit trail. Enterprise solutions start at $500/month."* — r/construction

**Target User:** Construction site supervisors, safety officers, and facilities managers at small-to-mid-sized firms.

**The WOW Moment:** A supervisor opens the app on their phone, selects the inspection type, taps through a structured checklist, attaches photos from the camera roll, and submits. The office manager sees the completed inspection report in real time on the dashboard, with all findings tagged by severity and linked to a remediation task.

**Master Prompt for IBM Project Bob:**
```
Build a Field Inspection Logger for construction site supervisors and safety officers.

Problem: Safety inspections are done on paper forms with phone photos. There is no 
searchable history, no remediation tracking, and no audit trail. Enterprise solutions 
are too expensive for small-to-mid-sized firms.

Tech Stack:
- Frontend: React with Tailwind CSS (mobile-first design)
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Organizations: id, name, created_at
- Users: id, org_id, name, email, role (ENUM: admin, supervisor, viewer), created_at
- Sites: id, org_id, name, address, created_at
- InspectionTemplates: id, org_id, name, checklist_items (JSONB), created_at
- Inspections: id, site_id, inspector_id, template_id, status (ENUM: draft, submitted, reviewed),
  submitted_at, reviewed_by, created_at
- InspectionFindings: id, inspection_id, checklist_item_ref, finding_text, 
  severity (ENUM: low, medium, high, critical), photo_urls TEXT[], 
  remediation_status (ENUM: open, in_progress, resolved), created_at

Core Features:
1. Mobile-optimized inspection form with photo attachment
2. Real-time dashboard showing open findings by site and severity
3. Remediation task assignment and status tracking
4. PDF report generation for completed inspections
5. Role-based access (admin, supervisor, viewer)

UI Requirements:
- Large tap targets for field use with gloves
- Offline-capable form submission with sync on reconnect
- Color-coded severity badges (green/yellow/orange/red)

The application must include a full audit log of all status changes and role-based 
access control enforced at the API level.
```

---

## Archetype 5: The Contractor Invoice Tracker

**Reddit Signal:** *"I'm a freelance developer. I have 8 active clients, 23 open invoices across different stages, and I track all of it in a spreadsheet. I've missed 3 late payment follow-ups this quarter because I forgot to check. Every invoicing tool I've tried is either $50/month or designed for a full accounting department."* — r/freelance

**Target User:** Freelancers, independent contractors, and solo consultants.

**The WOW Moment:** The dashboard shows a pipeline view of all invoices by status (draft, sent, overdue, paid), with a red "Overdue" badge on any invoice past its due date and an automatic follow-up email draft pre-populated and ready to send in one click.

**Master Prompt for IBM Project Bob:**
```
Build a Contractor Invoice Tracker for freelancers and independent contractors.

Problem: Freelancers track invoices in spreadsheets and miss late payment follow-ups. 
Full accounting tools are too expensive and complex for solo operators.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Contractors: id, name, email, password_hash, business_name, default_payment_terms_days,
  created_at
- Clients: id, contractor_id, name, email, company, billing_address, created_at
- Projects: id, contractor_id, client_id, name, description, hourly_rate, 
  status (ENUM: active, completed, on_hold), created_at
- Invoices: id, contractor_id, client_id, project_id, invoice_number, 
  issue_date DATE, due_date DATE, status (ENUM: draft, sent, overdue, paid, cancelled),
  subtotal NUMERIC(10,2), tax_rate NUMERIC(5,2), total NUMERIC(10,2), 
  paid_at TIMESTAMP, notes TEXT, created_at
- InvoiceLineItems: id, invoice_id, description TEXT, quantity NUMERIC(8,2), 
  unit_price NUMERIC(10,2), amount NUMERIC(10,2)
- PaymentReminders: id, invoice_id, sent_at TIMESTAMP, reminder_type VARCHAR(50)

Core Features:
1. Pipeline dashboard: invoices grouped by status with total value per column
2. One-click overdue follow-up email draft generation
3. Invoice PDF generation with contractor branding
4. Automatic status transition to 'overdue' based on due date
5. Revenue summary by client and by month

UI Requirements:
- Kanban-style pipeline view as the primary interface
- Invoice detail view with line item editor
- Client portal link for clients to view and confirm receipt

The application must include automatic overdue detection via a scheduled background 
job and a complete payment history log per client.
```

---

## Archetype 6: The Small Clinic Waitlist

**Reddit Signal:** *"I run a small dental practice. We have a paper waitlist for cancellation slots. When someone cancels, my receptionist has to call down the list one by one. Half the time the slot goes unfilled. There has to be a better way that doesn't cost $300/month."* — r/smallbusiness

**Target User:** Independent medical, dental, and wellness practices with 1–5 providers.

**The WOW Moment:** A patient cancels their appointment. The system automatically sends an SMS to the next 3 patients on the waitlist for that provider and time slot. The first to respond gets the slot. The receptionist sees the filled slot on the dashboard without making a single phone call.

**Master Prompt for IBM Project Bob:**
```
Build a Small Clinic Waitlist Manager for independent medical and dental practices.

Problem: Small practices manage cancellation waitlists on paper. When a slot opens, 
staff must call patients one by one. Slots go unfilled. Enterprise scheduling systems 
start at $300+/month.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Practices: id, name, address, phone, created_at
- Providers: id, practice_id, name, specialty, created_at
- Patients: id, practice_id, name, email, phone, sms_opt_in BOOLEAN, created_at
- AppointmentSlots: id, provider_id, start_time TIMESTAMPTZ, end_time TIMESTAMPTZ,
  appointment_type VARCHAR(100), status (ENUM: available, booked, cancelled), 
  booked_patient_id INTEGER REFERENCES patients(id), created_at
- WaitlistEntries: id, patient_id, provider_id, appointment_type, 
  preferred_days TEXT[], preferred_times TEXT[], priority_score INTEGER,
  status (ENUM: active, notified, booked, expired), created_at
- Notifications: id, waitlist_entry_id, slot_id, sent_at TIMESTAMP, 
  response VARCHAR(20), responded_at TIMESTAMP

Core Features:
1. Provider schedule view with cancellation detection
2. Automatic SMS blast to top 3 waitlist patients when a slot opens
3. First-response claim: first patient to reply "YES" gets the slot
4. Waitlist management: add, prioritize, and remove patients
5. Daily summary report for practice manager

UI Requirements:
- Provider daily schedule as the primary view
- Waitlist panel showing queue position and notification status
- One-click manual slot release with automatic notification trigger

The application must include SMS delivery tracking and a conflict prevention 
mechanism to prevent double-booking when multiple patients respond simultaneously.
```

---

## Archetype 7: The Pet Medication Tracker

**Reddit Signal:** *"My dog is on 4 medications. My cat is on 2. I have a sticky note on the fridge that I keep forgetting to check. I've tried human medication apps and they don't work for animals — they ask for things like 'prescribing physician' and 'pharmacy.' I just need something simple."* — r/AppIdeas (22 similar posts catalogued)

**Target User:** Pet owners with animals on multiple medications or complex care schedules.

**The WOW Moment:** The home screen shows a card for each pet with today's medication schedule. Overdue doses are highlighted in red. One tap marks a dose as given. The history view shows a 30-day compliance calendar — green for on-time, yellow for late, red for missed.

**Master Prompt for IBM Project Bob:**
```
Build a Pet Medication Tracker for pet owners managing multiple animals on complex 
medication schedules.

Problem: Human medication apps require fields like 'prescribing physician' and 
'pharmacy' that don't apply to pets. Pet owners need a simple, purpose-built 
tracker for animal medications.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL

Database Schema:
- Users: id, email, password_hash, timezone, created_at
- Pets: id, user_id, name, species, breed, weight_lbs, date_of_birth, 
  photo_url, created_at
- Medications: id, pet_id, name, dosage, dosage_unit, instructions, 
  prescribing_vet VARCHAR(255), refill_date DATE, 
  status (ENUM: active, completed, discontinued), created_at
- DoseSchedules: id, medication_id, frequency_type (ENUM: daily, twice_daily, 
  weekly, as_needed, custom), times_of_day TEXT[], days_of_week TEXT[], 
  start_date DATE, end_date DATE
- DoseLog: id, medication_id, scheduled_time TIMESTAMPTZ, given_at TIMESTAMPTZ, 
  given_by VARCHAR(100), notes TEXT, status (ENUM: on_time, late, missed, skipped)

Core Features:
1. Today's schedule view: all pets, all medications, all doses for today
2. One-tap dose logging with optional notes
3. 30-day compliance calendar per medication
4. Refill reminder alerts based on refill_date
5. Push notification reminders for upcoming doses

UI Requirements:
- Pet cards with photo and today's dose count on the home screen
- Large, thumb-friendly dose confirmation buttons
- Color-coded compliance calendar (green/yellow/red)

The application must support multiple pets per account and include a 
caregiver sharing feature so multiple family members can log doses.
```

---

## Archetype 8: The Meeting Action Extractor

**Reddit Signal:** *"I use Fireflies and Otter. Both give me a wall of text. I still have to read the entire 45-minute transcript to find the 3 things I need to do. I want something that extracts action items sorted by who's responsible, not just a transcript."* — r/AppIdeas (26 similar posts)

**Target User:** Team leads, project managers, and anyone who runs recurring meetings.

**The WOW Moment:** A meeting transcript is pasted in (or uploaded). Within seconds, the app displays a structured action item list — each item with an owner, a due date suggestion, and a priority level — grouped by person. One click exports it as a formatted Slack message or email.

**Master Prompt for IBM Project Bob:**
```
Build a Meeting Action Extractor for team leads and project managers.

Problem: Transcription tools produce walls of text. Users must read entire transcripts 
to find action items. There is no tool that extracts, structures, and assigns action 
items automatically, sorted by owner.

Tech Stack:
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL
- AI Integration: OpenAI API for action item extraction

Database Schema:
- Users: id, email, password_hash, created_at
- Meetings: id, user_id, title, meeting_date DATE, transcript_text TEXT, 
  duration_minutes INTEGER, status (ENUM: processing, complete, error), created_at
- Participants: id, meeting_id, name, email, created_at
- ActionItems: id, meeting_id, owner_id INTEGER REFERENCES participants(id),
  description TEXT, due_date DATE, priority (ENUM: low, medium, high),
  status (ENUM: open, in_progress, done), source_quote TEXT, created_at

Core Features:
1. Transcript paste/upload interface
2. AI-powered action item extraction with owner attribution
3. Action item list grouped by owner with edit capability
4. One-click export as formatted Slack message, email, or Markdown
5. Meeting history with searchable action item archive

UI Requirements:
- Split view: transcript on the left, extracted action items on the right
- Owner filter to see only your action items
- Inline editing of extracted items before export

The application must include a confidence score for each extracted action item 
and allow users to accept, edit, or reject each one before saving.
```
