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

user_problem_statement: "Import/build latest GitHub main branch from midnightchordz-lab/Swim and run existing SwarmSim app with private-beta sign-in landing, server-side auth endpoints, evidence ledger, ensemble forecast, scenario templates, replay timeline, and god-view injection UI. Verify /api/auth/me returns 401 Authentication required, frontend no longer serves static/js/main.4efc86c3.js, and first page shows private-beta sign-in landing."
backend:
  - task: "Import latest GitHub main backend and verify auth endpoint"
    implemented: true
    working: true
    file: "backend/server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Downloaded latest main archive from midnightchordz-lab/Swim, overlaid backend while preserving backend/.env, fixed missing AsyncIOScheduler import required for backend startup, installed requirements, and restarted supervisor services. Need testing agent to verify GET /api/auth/me returns 401 with detail Authentication required and not 404."
      - working: true
        agent: "testing"
        comment: "Backend testing completed successfully. GET /api/auth/me returns HTTP 401 with JSON detail 'Authentication required' as expected (not 404). Service health check passed - backend running on https://predict.preview.emergentagent.com/api with status 'ok'. Auth endpoint properly configured and working correctly."
frontend:
  - task: "Import latest GitHub main frontend and verify private-beta auth landing"
    implemented: true
    working: "NA"
    file: "frontend/src/App.js, frontend/src/components/AuthLandingGate.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Downloaded latest main archive from midnightchordz-lab/Swim, overlaid frontend while preserving frontend/.env, installed dependencies with yarn, and restarted frontend. Need frontend verification that the initial page is the private-beta sign-in landing and no static/js/main.4efc86c3.js bundle is served."
metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 2
  run_ui: true
test_plan:
  current_focus:
    - "Import latest GitHub main backend and verify auth endpoint"
    - "Import latest GitHub main frontend and verify private-beta auth landing"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"
agent_communication:
  - agent: "main"
    message: "Latest main archive was imported via GitHub tarball, not git write operations. Protected .git, .emergent, backend/.env, frontend/.env, and test_result.md were preserved. Services restarted and are running. Backend tester should verify /api/auth/me status/body. Frontend tester should verify private-beta sign-in landing and absence of old main.4efc86c3.js bundle."
  - agent: "testing"
    message: "Backend testing completed successfully. Auth endpoint verification passed - GET /api/auth/me returns HTTP 401 with JSON detail 'Authentication required' (not 404). Service health check confirmed backend is running properly on https://predict.preview.emergentagent.com/api. The imported latest main backend is working correctly."
