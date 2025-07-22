#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: "Erstelle eine App für einen Steinmetzbetrieb, die den Nutzer ein PDF eines Auftrages hochladen lässt um diesen dann später über ein Suchfeld gefiltert nach Auftragsnummer, Namen des Kunden oder Angabe eines verwendeten Steines finden zu können."

backend:
  - task: "PDF Upload API"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented PDF upload endpoint with text extraction using pdfplumber library"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: PDF upload API working perfectly. Successfully uploads PDF files, validates file types (rejects non-PDF), extracts text using pdfplumber, and stores base64 content in MongoDB. Tested with German content including 'Auftragsnummer: A-2023-001', 'Kunde: Max Mustermann', 'Steinart: Granit'. Returns proper JSON response with order_id and extracted_info."
  
  - task: "PDF Text Extraction"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added pattern matching for order number, customer name, and stone type extraction"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Text extraction working excellently. Successfully extracts German patterns: Auftragsnummer/Auftrag (A-2023-001, B-2023-002, C-2023-003), Kunde/Auftraggeber (Max Mustermann, Anna Schmidt, Hans Mueller), Steinart/Material (Granit, Marmor, Kalkstein). Regex patterns handle various German formats correctly. All test cases passed with accurate extraction."
  
  - task: "Search Orders API"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Implemented search API with support for filtering by order_number, customer_name, stone_type, or all fields"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: Search API working perfectly. All search types functional: order_number search (found 1 result for 'A-2023'), customer_name search (found 1 result for 'Max'), stone_type search (found 1 result for 'Granit'), all fields search (found 3 results for '2023'). Case-insensitive regex search working correctly. Returns proper JSON with results array and count."
  
  - task: "Order Management APIs"
    implemented: true
    working: true
    file: "/app/backend/server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added GET all orders, GET single order, and DELETE order endpoints"
      - working: true
        agent: "testing"
        comment: "✅ TESTED: All order management APIs working correctly. GET /api/orders retrieves all orders (tested with 3 orders), GET /api/order/{id} retrieves specific order by UUID, DELETE /api/order/{id} successfully deletes orders with proper German success message. All endpoints return appropriate HTTP status codes and JSON responses. MongoDB integration working properly."

frontend:
  - task: "PDF Upload Interface"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Created beautiful stone-themed upload interface with file validation"
  
  - task: "Search Interface"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented search interface with dropdown for search type selection"
  
  - task: "Orders Display"
    implemented: true
    working: true
    file: "/app/frontend/src/App.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Added order cards with professional styling and delete functionality"
  
  - task: "Stone Mason Themed UI"
    implemented: true
    working: true
    file: "/app/frontend/src/App.css"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "Created professional stone mason theme with granite/marble backgrounds"

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: true

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Implemented complete Steinmetz app with PDF upload, text extraction using pdfplumber, and search functionality. Frontend working with stone-themed design. Backend needs testing for PDF processing and search APIs."
  - agent: "testing"
    message: "✅ BACKEND TESTING COMPLETE: All backend APIs tested and working perfectly! Created comprehensive backend_test.py with 11 test cases. PDF upload with German text extraction (100% success), search functionality across all fields (100% success), and order management APIs (100% success). MongoDB integration working correctly. All 11 tests passed with 100% success rate. Backend is production-ready."