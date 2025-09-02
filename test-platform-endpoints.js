#!/usr/bin/env node

/**
 * Test script to verify all platform endpoints are working correctly
 */

const https = require('https');

const API_BASE = 'https://api.mapmystandards.ai';
const TEST_EMAIL = 'testuser@example.com';
const TEST_PASSWORD = 'TestPassword123!';

let authToken = null;

function makeRequest(method, path, data = null, headers = {}) {
    return new Promise((resolve, reject) => {
        const url = new URL(API_BASE + path);
        
        const options = {
            hostname: url.hostname,
            port: 443,
            path: url.pathname + url.search,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            
            res.on('data', (chunk) => {
                body += chunk;
            });
            
            res.on('end', () => {
                try {
                    const response = JSON.parse(body);
                    resolve({ status: res.statusCode, data: response });
                } catch (e) {
                    resolve({ status: res.statusCode, data: body });
                }
            });
        });
        
        req.on('error', reject);
        
        if (data) {
            req.write(JSON.stringify(data));
        }
        
        req.end();
    });
}

async function testEndpoints() {
    console.log('🔍 Testing MapMyStandards Platform Endpoints\n');
    
    // Test 1: Login
    console.log('1. Testing Login...');
    try {
        const loginResponse = await makeRequest('POST', '/auth/login', {
            email: TEST_EMAIL,
            password: TEST_PASSWORD
        });
        
        if (loginResponse.status === 200 && loginResponse.data.success) {
            console.log('✅ Login successful');
            authToken = loginResponse.data.data.access_token;
            console.log('   Token:', authToken.substring(0, 20) + '...');
        } else {
            console.log('❌ Login failed:', loginResponse.data);
            return;
        }
    } catch (error) {
        console.log('❌ Login error:', error.message);
        return;
    }
    
    // Test 2: Verify Token
    console.log('\n2. Testing Token Verification...');
    try {
        const verifyResponse = await makeRequest('GET', '/auth/verify-token', null, {
            'Authorization': `Bearer ${authToken}`
        });
        
        if (verifyResponse.status === 200) {
            console.log('✅ Token verified successfully');
            console.log('   Response:', JSON.stringify(verifyResponse.data, null, 2));
        } else {
            console.log('❌ Token verification failed:', verifyResponse.data);
        }
    } catch (error) {
        console.log('❌ Token verification error:', error.message);
    }
    
    // Test 3: Dashboard Overview
    console.log('\n3. Testing Dashboard Overview...');
    try {
        const dashboardResponse = await makeRequest('GET', '/api/dashboard/overview', null, {
            'Authorization': `Bearer ${authToken}`
        });
        
        if (dashboardResponse.status === 200) {
            console.log('✅ Dashboard overview retrieved successfully');
            console.log('   Data:', JSON.stringify(dashboardResponse.data, null, 2));
        } else {
            console.log('❌ Dashboard overview failed:', dashboardResponse.status, dashboardResponse.data);
        }
    } catch (error) {
        console.log('❌ Dashboard overview error:', error.message);
    }
    
    // Test 4: Dashboard Analytics
    console.log('\n4. Testing Dashboard Analytics...');
    try {
        const analyticsResponse = await makeRequest('GET', '/api/dashboard/analytics', null, {
            'Authorization': `Bearer ${authToken}`
        });
        
        if (analyticsResponse.status === 200) {
            console.log('✅ Dashboard analytics retrieved successfully');
            console.log('   Data:', JSON.stringify(analyticsResponse.data, null, 2));
        } else {
            console.log('❌ Dashboard analytics failed:', analyticsResponse.status, analyticsResponse.data);
        }
    } catch (error) {
        console.log('❌ Dashboard analytics error:', error.message);
    }
    
    // Test 5: Metrics Dashboard
    console.log('\n5. Testing Metrics Dashboard...');
    try {
        const metricsResponse = await makeRequest('GET', '/api/metrics/dashboard', null, {
            'Authorization': `Bearer ${authToken}`
        });
        
        if (metricsResponse.status === 200) {
            console.log('✅ Metrics dashboard retrieved successfully');
            console.log('   Data:', JSON.stringify(metricsResponse.data, null, 2));
        } else {
            console.log('❌ Metrics dashboard failed:', metricsResponse.status, metricsResponse.data);
        }
    } catch (error) {
        console.log('❌ Metrics dashboard error:', error.message);
    }
    
    console.log('\n✨ Testing complete!');
}

// Run the tests
testEndpoints().catch(console.error);
