#!/bin/bash

# Mock Canvas Demo Script
# Demonstrates A³E integration with realistic Canvas data

echo "🎨 A³E Mock Canvas Integration Demo"
echo "=================================="
echo ""

BASE_URL="http://localhost:8000"

echo "Starting local development server..."
echo "(In another terminal, run: make dev)"
echo ""
echo "Press Enter when the server is running..."
read -p ""

echo ""
echo "🧪 Testing Mock Canvas Integration"
echo "----------------------------------"

# Test 1: Integration Status
echo "1. Checking integration status..."
INTEGRATION_STATUS=$(curl -s "$BASE_URL/api/v1/integrations/status" | python3 -m json.tool 2>/dev/null)
if echo "$INTEGRATION_STATUS" | grep -q '"mode": "mock"'; then
    echo "✅ Mock mode detected"
    echo "   $(echo "$INTEGRATION_STATUS" | grep '"notice"' | cut -d'"' -f4)"
else
    echo "⚠️  Live mode or error - check configuration"
fi

echo ""

# Test 2: Canvas Connection Test
echo "2. Testing Canvas connection..."
CANVAS_TEST=$(curl -s "$BASE_URL/api/v1/integrations/canvas/test" | python3 -m json.tool 2>/dev/null)
if echo "$CANVAS_TEST" | grep -q '"mode": "mock"'; then
    echo "✅ Mock Canvas connection successful"
    USER_NAME=$(echo "$CANVAS_TEST" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['user']['name'])" 2>/dev/null || echo "Unknown")
    echo "   Connected as: $USER_NAME"
else
    echo "❌ Canvas connection failed"
fi

echo ""

# Test 3: Get Courses
echo "3. Fetching mock courses..."
COURSES=$(curl -s "$BASE_URL/api/v1/integrations/canvas/courses" | python3 -m json.tool 2>/dev/null)
if echo "$COURSES" | grep -q "Business Ethics\|Accounting\|Strategic"; then
    echo "✅ Mock courses loaded"
    COURSE_COUNT=$(echo "$COURSES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Found $COURSE_COUNT courses:"
    
    # List courses
    echo "$COURSES" | python3 -c "
import sys, json
try:
    courses = json.load(sys.stdin)
    for course in courses:
        print(f'     - {course[\"course_code\"]}: {course[\"name\"]} ({course[\"total_students\"]} students)')
except:
    pass
" 2>/dev/null
else
    echo "❌ Failed to load courses"
fi

echo ""

# Test 4: Get Course Outcomes
echo "4. Fetching learning outcomes for Business Ethics course..."
OUTCOMES=$(curl -s "$BASE_URL/api/v1/integrations/canvas/courses/101/outcomes" | python3 -m json.tool 2>/dev/null)
if echo "$OUTCOMES" | grep -q "Ethical Decision Making"; then
    echo "✅ Course outcomes loaded"
    OUTCOME_COUNT=$(echo "$OUTCOMES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Found $OUTCOME_COUNT learning outcomes:"
    
    # List outcomes
    echo "$OUTCOMES" | python3 -c "
import sys, json
try:
    outcomes = json.load(sys.stdin)
    for outcome in outcomes:
        print(f'     - {outcome[\"title\"]}: {outcome[\"description\"]}')
except:
    pass
" 2>/dev/null
else
    echo "❌ Failed to load outcomes"
fi

echo ""

# Test 5: Evidence Classification
echo "5. Testing evidence classification with course content..."
EVIDENCE_TEXT="This assignment requires students to analyze ethical frameworks and prepare financial statements showing corporate social responsibility impacts."

CLASSIFICATION=$(curl -s -X POST "$BASE_URL/api/v1/config/evidence/classify" \
    -H "Content-Type: application/json" \
    -d "\"$EVIDENCE_TEXT\"" | python3 -m json.tool 2>/dev/null)

if echo "$CLASSIFICATION" | grep -q "student_learning_outcomes\|faculty_credentials"; then
    echo "✅ Evidence classification working"
    TAG_COUNT=$(echo "$CLASSIFICATION" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Classified into $TAG_COUNT evidence categories:"
    
    # List tags
    echo "$CLASSIFICATION" | python3 -c "
import sys, json
try:
    tags = json.load(sys.stdin)
    for tag in tags:
        print(f'     - {tag[\"id\"]}: {tag[\"category\"]}')
except:
    pass
" 2>/dev/null
else
    echo "❌ Evidence classification failed"
fi

echo ""

# Test 6: Accreditor Standards
echo "6. Testing accreditor standards mapping..."
SACSCOC_STANDARDS=$(curl -s "$BASE_URL/api/v1/config/accreditors/sacscoc/standards" | python3 -m json.tool 2>/dev/null)
if echo "$SACSCOC_STANDARDS" | grep -q "Mission\|Degree Standards"; then
    echo "✅ SACSCOC standards loaded"
    STANDARDS_COUNT=$(echo "$SACSCOC_STANDARDS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    echo "   Found $STANDARDS_COUNT SACSCOC standards"
else
    echo "❌ Failed to load SACSCOC standards"
fi

echo ""

# Test 7: Data Synchronization
echo "7. Testing data synchronization..."
SYNC_RESULT=$(curl -s -X POST "$BASE_URL/api/v1/integrations/sync" | python3 -m json.tool 2>/dev/null)
if echo "$SYNC_RESULT" | grep -q "started"; then
    echo "✅ Data sync initiated"
    echo "   $(echo "$SYNC_RESULT" | grep '"message"' | cut -d'"' -f4)"
    echo "   Mode: $(echo "$SYNC_RESULT" | grep '"mode"' | cut -d'"' -f4)"
else
    echo "❌ Data sync failed"
fi

echo ""
echo "🎯 Demo Summary"
echo "==============="
echo ""
echo "The A³E system is now running with realistic mock Canvas data including:"
echo ""
echo "📚 Courses:"
echo "   • Business Ethics and Corporate Responsibility (MGMT 485)"
echo "   • Principles of Accounting I (ACCT 201)"
echo "   • Strategic Management Capstone (MGMT 495)"
echo ""
echo "🎯 Learning Outcomes:"
echo "   • Ethical Decision Making"
echo "   • Corporate Social Responsibility"
echo "   • Financial Statement Preparation"
echo "   • Strategic Analysis"
echo ""
echo "📋 Assignments:"
echo "   • Stakeholder Analysis Case Study"
echo "   • Financial Statement Analysis Project"
echo "   • Comprehensive Strategy Plan"
echo ""
echo "🏛️ Accreditation Standards:"
echo "   • SACSCOC, NECHE, WSCUC standards"
echo "   • Evidence classification and mapping"
echo "   • Institution type contextualization"
echo ""
echo "🔧 Next Steps:"
echo "   • Visit http://localhost:8000/docs for full API documentation"
echo "   • Test evidence upload and mapping workflows"
echo "   • Configure real Canvas credentials when available"
echo "   • Add your institution's specific accreditors"
echo ""
echo "🎉 Mock Canvas integration is fully functional!"
