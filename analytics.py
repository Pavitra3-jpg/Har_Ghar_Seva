from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import users_db, jobs_db, applications_db, ratings_db, messages_db
from datetime import datetime, timedelta
from collections import defaultdict

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics for current user"""
    if current_user.user_type == 'worker':
        return worker_stats()
    elif current_user.user_type == 'provider':
        return provider_stats()
    elif current_user.user_type == 'admin':
        return admin_stats()
    
    return jsonify({'error': 'Invalid user type'})

def worker_stats():
    """Get statistics for worker dashboard"""
    user_applications = [app for app in applications_db.values() if app.worker_id == current_user.id]
    user_ratings = [rating for rating in ratings_db.values() if rating.rated_id == current_user.id]
    user_messages = [msg for msg in messages_db.values() 
                    if msg.sender_id == current_user.id or msg.recipient_id == current_user.id]
    
    # Calculate statistics
    stats = {
        'total_applications': len(user_applications),
        'accepted_applications': len([app for app in user_applications if app.status == 'accepted']),
        'pending_applications': len([app for app in user_applications if app.status == 'pending']),
        'success_rate': calculate_success_rate(user_applications),
        'average_rating': current_user.rating or 0,
        'total_reviews': len(user_ratings),
        'total_messages': len(user_messages),
        'profile_completion': calculate_profile_completion(current_user)
    }
    
    return jsonify(stats)

def provider_stats():
    """Get statistics for job provider"""
    user_jobs = [job for job in jobs_db.values() if job.provider_id == current_user.id]
    all_applications = []
    for job in user_jobs:
        job_applications = [app for app in applications_db.values() if app.job_id == job.id]
        all_applications.extend(job_applications)
    
    stats = {
        'total_jobs_posted': len(user_jobs),
        'active_jobs': len([job for job in user_jobs if job.status == 'open']),
        'total_applications': len(all_applications),
        'average_applications_per_job': len(all_applications) / len(user_jobs) if user_jobs else 0,
        'most_popular_job': get_most_popular_job(user_jobs),
        'hiring_rate': calculate_hiring_rate(all_applications)
    }
    
    return jsonify(stats)

def admin_stats():
    """Get platform-wide statistics for admin"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_users': len(users_db),
        'total_workers': len([u for u in users_db.values() if u.user_type == 'worker']),
        'total_providers': len([u for u in users_db.values() if u.user_type == 'provider']),
        'verified_workers': len([u for u in users_db.values() if u.user_type == 'worker' and u.is_verified]),
        'total_jobs': len(jobs_db),
        'active_jobs': len([j for j in jobs_db.values() if j.status == 'open']),
        'total_applications': len(applications_db),
        'total_ratings': len(ratings_db),
        'new_users_this_week': count_new_users(week_ago),
        'new_jobs_this_week': count_new_jobs(week_ago),
        'platform_activity': calculate_platform_activity()
    }
    
    return jsonify(stats)

@analytics_bp.route('/api/chart_data/<chart_type>')
@login_required
def get_chart_data(chart_type):
    """Get data for various charts"""
    if chart_type == 'applications_timeline':
        return jsonify(get_applications_timeline())
    elif chart_type == 'skills_demand':
        return jsonify(get_skills_demand())
    elif chart_type == 'rating_distribution':
        return jsonify(get_rating_distribution())
    elif chart_type == 'job_categories':
        return jsonify(get_job_categories())
    
    return jsonify({'error': 'Invalid chart type'})

def calculate_success_rate(applications):
    """Calculate application success rate"""
    if not applications:
        return 0
    accepted = len([app for app in applications if app.status == 'accepted'])
    return round((accepted / len(applications)) * 100, 1)

def calculate_profile_completion(user):
    """Calculate profile completion percentage"""
    fields = ['username', 'email', 'location', 'skills', 'experience_years', 
              'hourly_wage', 'profile_photo', 'id_proof']
    completed = sum(1 for field in fields if getattr(user, field, None))
    return round((completed / len(fields)) * 100)

def calculate_hiring_rate(applications):
    """Calculate hiring rate for providers"""
    if not applications:
        return 0
    hired = len([app for app in applications if app.status == 'accepted'])
    return round((hired / len(applications)) * 100, 1)

def get_most_popular_job(jobs):
    """Get the job with most applications"""
    if not jobs:
        return None
    
    job_app_counts = {}
    for job in jobs:
        app_count = len([app for app in applications_db.values() if app.job_id == job.id])
        job_app_counts[job.id] = app_count
    
    if job_app_counts:
        most_popular_id = max(job_app_counts, key=job_app_counts.get)
        return jobs_db[most_popular_id].title
    
    return None

def count_new_users(since_date):
    """Count new users since a specific date"""
    return len([u for u in users_db.values() if u.created_at >= since_date])

def count_new_jobs(since_date):
    """Count new jobs since a specific date"""
    return len([j for j in jobs_db.values() if j.created_at >= since_date])

def calculate_platform_activity():
    """Calculate platform activity score"""
    week_ago = datetime.now() - timedelta(days=7)
    
    recent_applications = len([app for app in applications_db.values() 
                              if app.created_at >= week_ago])
    recent_messages = len([msg for msg in messages_db.values() 
                          if msg.created_at >= week_ago])
    recent_ratings = len([rating for rating in ratings_db.values() 
                         if rating.created_at >= week_ago])
    
    # Simple activity score based on recent activity
    activity_score = (recent_applications * 3) + (recent_messages * 1) + (recent_ratings * 2)
    return min(activity_score, 100)  # Cap at 100

def get_applications_timeline():
    """Get applications data for timeline chart"""
    timeline = defaultdict(int)
    for app in applications_db.values():
        date_key = app.created_at.strftime('%Y-%m-%d')
        timeline[date_key] += 1
    
    # Get last 7 days
    dates = []
    counts = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        dates.append(date)
        counts.append(timeline.get(date, 0))
    
    return {'labels': dates, 'data': counts}

def get_skills_demand():
    """Get skills demand data"""
    skill_counts = defaultdict(int)
    
    # Count skills required in jobs
    for job in jobs_db.values():
        if job.skills_required:
            for skill in job.skills_required:
                skill_counts[skill.lower()] += 1
    
    # Get top 10 skills
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'labels': [skill[0].title() for skill in top_skills],
        'data': [skill[1] for skill in top_skills]
    }

def get_rating_distribution():
    """Get rating distribution data"""
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for rating in ratings_db.values():
        rating_counts[rating.rating] += 1
    
    return {
        'labels': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
        'data': [rating_counts[i] for i in range(1, 6)]
    }

def get_job_categories():
    """Get job categories data"""
    categories = defaultdict(int)
    
    for job in jobs_db.values():
        category = job.category if hasattr(job, 'category') else 'General'
        categories[category] += 1
    
    return {
        'labels': list(categories.keys()),
        'data': list(categories.values())
    }