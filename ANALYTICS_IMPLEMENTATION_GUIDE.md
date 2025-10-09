# 🚀 Analytics Implementation Guide

## 📋 **Step-by-Step Implementation**

### **Step 1: Create Database Tables**
Run these SQL commands in phpMyAdmin:

```sql
-- 1. Property Views Tracking
CREATE TABLE property_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    user_id INT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer VARCHAR(500),
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    INDEX idx_property_id (property_id),
    INDEX idx_user_id (user_id),
    INDEX idx_viewed_at (viewed_at),
    FOREIGN KEY (property_id) REFERENCES houses(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 2. Search Analytics
CREATE TABLE search_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    search_term VARCHAR(255),
    filters_applied JSON,
    results_count INT,
    ip_address VARCHAR(45),
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    INDEX idx_user_id (user_id),
    INDEX idx_searched_at (searched_at),
    INDEX idx_search_term (search_term),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 3. User Sessions
CREATE TABLE user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(100) UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL,
    session_duration INT NULL,
    pages_viewed INT DEFAULT 0,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_login_time (login_time),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Property Performance
CREATE TABLE property_performance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    date DATE NOT NULL,
    views_count INT DEFAULT 0,
    searches_count INT DEFAULT 0,
    contacts_count INT DEFAULT 0,
    featured_views INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_property_date (property_id, date),
    INDEX idx_property_id (property_id),
    INDEX idx_date (date),
    FOREIGN KEY (property_id) REFERENCES houses(id) ON DELETE CASCADE
);

-- 5. Revenue Analytics
CREATE TABLE revenue_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT NOT NULL,
    date DATE NOT NULL,
    daily_rent DECIMAL(10,2) DEFAULT 0,
    monthly_rent DECIMAL(10,2) DEFAULT 0,
    is_occupied BOOLEAN DEFAULT FALSE,
    occupancy_days INT DEFAULT 0,
    revenue_generated DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_property_date (property_id, date),
    INDEX idx_property_id (property_id),
    INDEX idx_date (date),
    FOREIGN KEY (property_id) REFERENCES houses(id) ON DELETE CASCADE
);

-- 6. Geographic Analytics
CREATE TABLE geographic_analytics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT NOT NULL,
    date DATE NOT NULL,
    property_views INT DEFAULT 0,
    property_searches INT DEFAULT 0,
    new_listings INT DEFAULT 0,
    average_price DECIMAL(10,2) DEFAULT 0,
    demand_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_region_date (region_id, date),
    INDEX idx_region_id (region_id),
    INDEX idx_date (date),
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE
);

-- 7. User Engagement Tracking
CREATE TABLE user_engagement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    login_count INT DEFAULT 0,
    session_duration INT DEFAULT 0,
    pages_viewed INT DEFAULT 0,
    properties_viewed INT DEFAULT 0,
    searches_performed INT DEFAULT 0,
    reports_submitted INT DEFAULT 0,
    engagement_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_date (user_id, date),
    INDEX idx_user_id (user_id),
    INDEX idx_date (date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### **Step 2: Initialize Analytics Data**
```bash
python initialize_analytics.py
```

### **Step 3: Add Tracking to Your Routes**

#### **A. Track Property Views**
Add this to your `house_detail` route in `modules/user_routes.py`:

```python
from modules.analytics_tracking import track_property_view, update_user_engagement

@user_bp.route('/house/<int:house_id>')
def house_detail(house_id):
    # ... existing code ...
    
    # Track property view
    track_property_view(
        property_id=house_id,
        user_id=session.get('user_id'),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        session_id=session.get('session_id')
    )
    
    # Update user engagement
    if session.get('user_id'):
        update_user_engagement(session['user_id'], 'property_view')
    
    # ... rest of existing code ...
```

#### **B. Track Search Activities**
Add this to your `houses` route in `modules/user_routes.py`:

```python
from modules.analytics_tracking import track_search, update_user_engagement

@user_bp.route('/houses')
def houses():
    # ... existing code ...
    
    # Track search if filters are applied
    if any([region_filter, property_type_filter, min_price, max_price, search_filter]):
        track_search(
            user_id=session.get('user_id'),
            search_term=search_filter,
            filters_applied={
                'region': region_filter,
                'property_type': property_type_filter,
                'min_price': min_price,
                'max_price': max_price
            },
            results_count=len(houses),
            ip_address=request.remote_addr,
            session_id=session.get('session_id')
        )
        
        # Update user engagement
        if session.get('user_id'):
            update_user_engagement(session['user_id'], 'search')
    
    # ... rest of existing code ...
```

#### **C. Track User Sessions**
Add this to your login route in `modules/auth.py`:

```python
from modules.analytics_tracking import track_user_session, update_user_engagement

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... existing code ...
    
    if user and check_password_hash(user['password_hash'], password):
        # ... existing login code ...
        
        # Track user session
        session_id = session.get('session_id', str(uuid.uuid4()))
        track_user_session(
            user_id=user['id'],
            session_id=session_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Update user engagement
        update_user_engagement(user['id'], 'login')
        
        # ... rest of existing code ...
```

### **Step 4: Access Enhanced Dashboard**
Visit: `http://localhost:5000/admin/enhanced-dashboard`

### **Step 5: Update Navigation**
Add a link to the enhanced dashboard in your admin navigation:

```html
<a href="/admin/enhanced-dashboard" class="nav-link">
    <i class="fas fa-chart-line nav-icon"></i>
    Enhanced Analytics
</a>
```

## 📊 **What You'll Get**

### **Revenue Analytics**
- Total revenue tracking
- Average rent by property type
- Top earning properties
- Revenue growth trends

### **User Engagement**
- Active users (daily/monthly)
- Engagement scores
- Session duration
- User retention rates

### **Property Performance**
- View counts per property
- Search-to-view conversion
- Most popular properties
- Performance by region/type

### **Geographic Analytics**
- Regional performance
- Demand patterns
- Price analysis by region
- Top performing areas

## 🔧 **Customization Options**

### **Add More Metrics**
Edit `modules/advanced_metrics.py` to add custom metrics.

### **Customize Dashboard**
Edit `templates/admin/enhanced_dashboard.html` to add more charts or metrics.

### **Set Up Automated Updates**
Create a cron job to run analytics updates:

```bash
# Add to crontab
0 1 * * * cd /path/to/your/project && python -c "from modules.analytics_tracking import initialize_analytics_data; initialize_analytics_data()"
```

## 🚨 **Important Notes**

1. **Performance**: Analytics queries can be heavy. Consider adding database indexes.
2. **Data Privacy**: Ensure you comply with data protection regulations.
3. **Backup**: Regular backups of analytics data are recommended.
4. **Monitoring**: Monitor database performance as data grows.

## 🎯 **Next Steps**

1. Implement the SQL tables
2. Run the initialization script
3. Add tracking to your routes
4. Test the enhanced dashboard
5. Monitor and optimize performance

Your analytics system is now ready to provide comprehensive insights into your rental platform! 🚀
