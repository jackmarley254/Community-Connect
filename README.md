Community Connect Platform

Modern Property Management. Made Simple.

📖 Overview

Community Connect is a bespoke, multi-tenant Property Management System (PMS) designed to digitize and automate the operations of residential real estate management. Built to solve the challenges of manual invoicing, delayed communication, and operational inefficiency, the platform serves as a centralized hub for four distinct stakeholders: Property Managers, Home Owners, Tenants, and Security Personnel.

This project was developed as a comprehensive solution for managing multiple properties, automating financial workflows, and ensuring real-time resident services.

🚀 Key Features

🏢 For Property Managers (Admin & Operations)

Unified Dashboard: A bird's-eye view of all managed properties with real-time Occupancy Metrics.

Multi-Tenancy: Scalable architecture allowing different organizations to manage their portfolios in isolation.

Bulk Unit Creator: A powerful tool to generate hundreds of units (e.g., "Units 101-200") in seconds.

Financial Oversight: Track paid vs. unpaid invoices across all buildings instantly.

Digital Notice Board: Post official announcements visible only to residents of specific properties.

🏠 For Home Owners (Landlords)

Financial Hub: A dedicated portal to view all service charge invoices, payment history, and due dates.

Asset Management: View owned units and manage parking lot assignments.

Tenant Invoicing: Ability to generate and send rent invoices directly to their current tenants.

👥 For Tenants (Residents)

Instant Alerts: Real-time notifications for visitors and package deliveries via a polling system linked to the Security Desk.

Maintenance Ticketing: Submit repair requests (e.g., "Leaking pipe") and track their status from 'Open' to 'Resolved'.

M-Pesa Integration (Simulated): "Pay Now" functionality for rent and service charge invoices.

🛡️ For Security Desk

Rapid Alert System: A simplified, focused interface for logging visitor arrivals and deliveries, triggering instant alerts on tenant dashboards.

🛠️ Technology Stack

Backend Framework: Django 5 (Python)

Frontend: Bootstrap 5, HTML5, CSS3

Interactivity: Vanilla JavaScript, Fetch API (AJAX)

Database: SQLite (Development) / PostgreSQL (Production ready)

Authentication: Custom Role-Based Access Control (RBAC)

⚙️ Installation & Setup

Follow these steps to run the project locally.

Prerequisites

Python 3.10+ installed

Virtual Environment (recommended)

1. Clone the Repository

git clone 
cd community-connect



2. Create and Activate Virtual Environment

# Windows
python -m venv myenv
myenv\Scripts\activate

# Mac/Linux
python3 -m venv myenv
source myenv/bin/activate



3. Install Dependencies

pip install django
# Or if you have a requirements.txt
# pip install -r requirements.txt



4. Apply Migrations

python manage.py makemigrations
python manage.py migrate



5. Create a Superuser (Admin)

python manage.py createsuperuser



6. Run the Server

python manage.py runserver



Visit http://127.0.0.1:8000/ in your browser.


Note: Ensure the Manager and Security users are linked to the same Organization.

🌍 Sustainable Development Goals (SDG) Alignment

This project aligns with SDG 11: Sustainable Cities and Communities.

Target 11.3: Enhances inclusive and sustainable urbanization by digitizing management processes.

Target 11.B: Improves resilience through efficient disaster/maintenance reporting systems.

📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

Developed by Jackson G. Ndiritu ICT Support Technician & Junior Software Developer