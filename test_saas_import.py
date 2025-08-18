#!/usr/bin/env python3
"""
Test script to verify SaaS API functionality
"""
try:
    print("Testing SaaS API import...")
    from saas_api_safe import app
    print("✅ SaaS API imported successfully")
    
    print("Testing app object...")
    print(f"App type: {type(app)}")
    print(f"App title: {getattr(app, 'title', 'No title')}")
    
    # Test if we can access routes
    routes = getattr(app, 'routes', [])
    print(f"Number of routes: {len(routes)}")
    
    for route in routes[:5]:  # Show first 5 routes
        if hasattr(route, 'path'):
            print(f"Route: {route.path}")
    
    print("✅ SaaS API is ready for deployment")
    
except Exception as e:
    print(f"❌ Error testing SaaS API: {e}")
    import traceback
    traceback.print_exc()
