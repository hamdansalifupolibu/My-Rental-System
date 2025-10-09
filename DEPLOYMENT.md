# 🚀 GhanaRentals Deployment Guide for Render

This guide will help you deploy your GhanaRentals application to Render hosting platform.

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Database**: You'll need a MySQL database (Render provides this)

## 🗄️ Database Setup

### Option 1: Render PostgreSQL (Recommended)
Render provides managed PostgreSQL databases. You'll need to update your database configuration.

### Option 2: External MySQL Database
You can use external MySQL services like:
- **PlanetScale** (MySQL-compatible)
- **Railway** (MySQL)
- **AWS RDS** (MySQL)

## 🔧 Environment Variables

Set these environment variables in your Render dashboard:

### Required Variables
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-change-this
DB_HOST=your-database-host
DB_USER=your-database-username
DB_PASSWORD=your-database-password
DB_NAME=ghana_rentals
DB_PORT=3306
PORT=10000
```

### Optional Variables
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Production ready deployment"
   git push origin main
   ```

2. **Verify all files are present**:
   - `requirements.txt` ✅
   - `wsgi.py` ✅
   - `render.yaml` ✅
   - `config_production.py` ✅

### Step 2: Create Render Web Service

1. **Go to Render Dashboard**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service**:
   - **Name**: `ghana-rentals`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application`
   - **Plan**: Free (or paid for better performance)

### Step 3: Set Environment Variables

In your Render service dashboard:

1. **Go to "Environment" tab**
2. **Add all required environment variables** (see list above)
3. **Make sure to set `FLASK_ENV=production`**

### Step 4: Create Database (if using Render)

1. **Go to Render Dashboard**
2. **Click "New +" → "PostgreSQL"**
3. **Configure**:
   - **Name**: `ghana-rentals-db`
   - **Database**: `ghana_rentals`
   - **User**: `ghana_rentals_user`
   - **Plan**: Free (or paid for better performance)

### Step 5: Update Database Configuration

If using PostgreSQL instead of MySQL, update your database configuration:

1. **Update `requirements.txt`**:
   ```
   psycopg2-binary==2.9.7
   ```

2. **Update `modules/database.py`** to use PostgreSQL:
   ```python
   import psycopg2
   
   def get_db_connection():
       conn = psycopg2.connect(
           host=os.environ.get('DB_HOST'),
           user=os.environ.get('DB_USER'),
           password=os.environ.get('DB_PASSWORD'),
           database=os.environ.get('DB_NAME'),
           port=os.environ.get('DB_PORT', 5432)
       )
       return conn
   ```

### Step 6: Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (5-10 minutes)
3. **Check logs** for any errors
4. **Test your application**

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: Database connection failed
```
**Solution**: Check your database credentials and ensure the database is accessible.

#### 2. Import Error
```
Error: No module named 'mysql.connector'
```
**Solution**: Make sure `mysql-connector-python` is in your `requirements.txt`.

#### 3. Static Files Not Loading
```
Error: CSS/JS files not loading
```
**Solution**: Check that your static files are properly referenced with `url_for()`.

#### 4. File Upload Issues
```
Error: Upload folder not found
```
**Solution**: Ensure the upload folder exists and has proper permissions.

### Debugging Steps

1. **Check Render Logs**:
   - Go to your service dashboard
   - Click "Logs" tab
   - Look for error messages

2. **Test Database Connection**:
   ```python
   # Add this to your app.py for testing
   @app.route('/test-db')
   def test_db():
       try:
           conn = get_db_connection()
           return "Database connection successful!"
       except Exception as e:
           return f"Database error: {e}"
   ```

3. **Check Environment Variables**:
   ```python
   # Add this to your app.py for testing
   @app.route('/test-env')
   def test_env():
       return {
           'DB_HOST': os.environ.get('DB_HOST'),
           'DB_NAME': os.environ.get('DB_NAME'),
           'FLASK_ENV': os.environ.get('FLASK_ENV')
       }
   ```

## 📊 Performance Optimization

### For Production

1. **Use Paid Plans**: Free plans have limitations
2. **Enable Caching**: Add Redis for session storage
3. **CDN**: Use Cloudflare for static assets
4. **Database Indexing**: Add indexes to frequently queried columns

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_houses_region ON houses(region);
CREATE INDEX idx_houses_type ON houses(property_type);
CREATE INDEX idx_houses_price ON houses(price);
CREATE INDEX idx_houses_created ON houses(created_at);
```

## 🔒 Security Considerations

1. **Change Default Secret Key**: Use a strong, random secret key
2. **Database Security**: Use strong passwords
3. **HTTPS**: Render provides SSL certificates automatically
4. **Environment Variables**: Never commit sensitive data to Git

## 📈 Monitoring

1. **Render Metrics**: Monitor CPU, memory, and response times
2. **Error Tracking**: Set up error monitoring (Sentry, etc.)
3. **Uptime Monitoring**: Use services like UptimeRobot

## 🔄 Updates and Maintenance

### Deploying Updates

1. **Push changes to GitHub**
2. **Render automatically redeploys**
3. **Check logs for any issues**

### Database Migrations

1. **Backup your database** before major changes
2. **Test migrations locally** first
3. **Run migrations** during maintenance windows

## 📞 Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Flask Documentation**: [flask.palletsprojects.com](https://flask.palletsprojects.com)
- **Community Support**: Stack Overflow, Reddit

## 🎉 Success Checklist

- [ ] Application deploys without errors
- [ ] Database connection works
- [ ] All pages load correctly
- [ ] User registration/login works
- [ ] File uploads work
- [ ] Admin dashboard accessible
- [ ] All links and navigation work
- [ ] Static files (CSS/JS) load
- [ ] Environment variables set correctly
- [ ] SSL certificate active

---

**Congratulations!** 🎉 Your GhanaRentals application should now be live on Render!
