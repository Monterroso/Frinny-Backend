# MongoDB Atlas Migration Guide

## Overview

This document outlines the process of migrating from a Docker-based MongoDB container to MongoDB Atlas for the Frinny Agent application. This migration will simplify debugging, reduce infrastructure complexity, and provide enhanced monitoring capabilities.

## 1. MongoDB Atlas Setup

### 1.1 Create MongoDB Atlas Account and Project
- [x] Sign up for a MongoDB Atlas account at [https://www.mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register)
- [x] Create a new project (e.g., "Frinny Agent")
- [x] Navigate to the Database section of your project

### 1.2 Create and Configure a Cluster
- [x] Click "Build a Database"
- [x] Select "FREE" tier option (M0 Sandbox)
- [x] Choose a cloud provider (AWS, GCP, or Azure) and region closest to your application servers
- [x] Name your cluster (e.g., "FrinnyDB")
- [x] Click "Create Cluster" (deployment takes a few minutes)

### 1.3 Set Up Database User
- [x] In the Security section, select "Database Access"
- [x] Click "Add New Database User"
- [x] Choose "Password" authentication method
- [x] Create a username and secure password
- [x] Set appropriate access: "Read and write to any database" for development
- [x] Add User

### 1.4 Configure Network Access
- [x] In the Security section, select "Network Access"
- [x] Click "Add IP Address"
- [x] For development: Add your current IP or use "Allow Access From Anywhere" (0.0.0.0/0)
- [x] For production: Restrict to server IP addresses

## 2. Connect Your Application

### 2.1 Get Connection String
- [x] Return to Database section and click "Connect" on your cluster
- [x] Select "Connect your application"
- [x] Choose "Python" as your driver and appropriate version
- [x] Copy the connection string

### 2.2 Update Environment Variables
- [x] Modify your `.env` file to include:
  ```
  MONGODB_USERNAME=<your_atlas_username>
  MONGODB_PASSWORD=<your_atlas_password>
  MONGODB_DATABASE=frinny_agent
  MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-address>/<database>?retryWrites=true&w=majority
  ```
- [x] Replace placeholder values with actual credentials
- [x] Keep database name as "frinny_agent" for compatibility

### 2.3 Update Docker Configuration
- [x] Edit `docker-compose.yml` to remove the MongoDB service
- [x] Update the web service to remove dependency on MongoDB service
- [x] Keep the MongoDB environment variables for the web service

## 3. Code Verification

### 3.1 Review Connection Code
- [x] Verify the MongoDB connection code in `app/agent/agent.py`
- [x] Ensure proper error handling for MongoDB connection failures
- [x] Consider adding explicit reconnection logic if needed

### 3.2 Update Any MongoDB-Specific Code
- [x] Atlas uses a replica set, so ensure your MongoDB connection parameters handle this
- [x] Verify timeout settings are appropriate for cloud-based connection
- [x] Ensure your code properly disconnects from MongoDB when appropriate

## 4. Testing

### 4.1 Local Testing
- [ ] Run application locally with Atlas MongoDB connection
- [ ] Verify logs show successful connection to MongoDB Atlas
- [ ] Test conversation persistence functionality
- [ ] Run tests specifically for MongoDB functionality:
  ```bash
  python tests/test_mongodb_persistence.py
  ```

### 4.2 Verify Data Storage
- [ ] In MongoDB Atlas, navigate to "Browse Collections"
- [ ] Select your database and collection
- [ ] Verify documents are being created and updated
- [ ] Check structure of stored documents matches expected format

### 4.3 Docker Environment Testing
- [ ] Rebuild and run Docker containers with updated configuration
- [ ] Test persistence functionality in containerized environment

## 5. Monitoring and Operations

### 5.1 Set Up Monitoring
- [ ] In MongoDB Atlas, review the monitoring tab
- [ ] Set up alerts for connection failures or high latency
- [ ] Configure Atlas metrics to track performance

### 5.2 Performance Optimization
- [ ] Review connection pooling settings
- [ ] Consider adding indexes for frequently queried fields
- [ ] Set appropriate TTL (Time To Live) index if documents should expire

### 5.3 Documentation Updates
- [ ] Update MongoDB.md with Atlas-specific information
- [ ] Document migration process for team members
- [ ] Update any architecture diagrams to reflect MongoDB Atlas

## 6. Troubleshooting Guide

### 6.1 Common Issues
- [ ] Connection timeout: Check network access settings and IP whitelist
- [ ] Authentication failure: Verify username/password and database permissions
- [ ] Write concerns: Make sure write concern level is appropriate
- [ ] Reconnection issues: Implement proper reconnection handling

### 6.2 Debugging Resources
- [ ] MongoDB Atlas logs (available in the Atlas UI)
- [ ] Application logs with connection information
- [ ] Performance metrics from the Atlas monitoring dashboard

## Benefits of MongoDB Atlas vs Self-Hosted

### Simplified Debugging
- Web-based UI dashboard to directly inspect collections, documents, and connections
- Built-in monitoring tools to see exactly when and how your application connects
- Query explorer to verify if data is being stored correctly
- Clear visibility into connection events and failures

### Reduced Complexity
- Eliminates Docker networking issues that can be difficult to diagnose
- No need to maintain the MongoDB container configuration
- Fewer moving parts in your Docker Compose setup

### Enhanced Features
- Automatic backups
- Scaling capabilities
- Performance insights
- Security management handled for you

### Direct Visibility for Persistence Issues
- Easier to debug as you can directly see if documents are being created

## Next Steps
After migration is complete, consider:
- [ ] Setting up regular database backups
- [ ] Implementing data migration strategies for future updates
- [ ] Creating read-only users for monitoring access 