import streamlit as st
import time
import json
import subprocess
import requests
from bs4 import BeautifulSoup

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
API_KEY = ""  # Replace with your Gemini API key

def call_gemini(prompt):
    """Call the Gemini model (via curl) with the given prompt."""
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    payload_json = json.dumps(payload)

    try:
        result = subprocess.run(
            [
                "curl",
                "-H", "Content-Type: application/json",
                "-d", payload_json,
                "-X", "POST",
                f"{API_URL}?key={API_KEY}"
            ],
            capture_output=True, text=True, check=True
        )

        # Parse the response
        response_json = json.loads(result.stdout)
        
        # Check if candidates exist and get the content from the first candidate
        if "candidates" in response_json and response_json["candidates"]:
            candidate = response_json["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                # Extract the generated content
                generated_content = candidate["content"]["parts"][0].get("text", "")
                return generated_content
            else:
                st.error("No 'content' or 'parts' found in candidate")
                return "No content returned from Gemini."
        else:
            st.error("No candidates found in response")
            return "No content returned from Gemini."

    except subprocess.CalledProcessError as e:
        st.error(f"An error occurred while calling Gemini: {e}")
        return f"An error occurred while calling Gemini: {e}"
    except json.JSONDecodeError as e:
        st.error(f"Error decoding response JSON: {e}")
        return f"Error decoding response JSON: {e}"

# Function to scrape requirements from a website
def requirements_gathering_from_website(url):
    """Scrape requirements or data from a given URL."""
    st.write(f"Scraping content from {url}...")
    try:
        # Send a request to the website
        response = requests.get(url)
        if response.status_code != 200:
            return f"Error: Could not fetch data from {url}"
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the main content (this is a placeholder, adjust based on your website structure)
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs])

        # Process the content with the AI model (if necessary)
        prompt = f"Extract the key requirements from this text: {content}"
        result = call_gemini(prompt)
        
        return result
    except Exception as e:
        return f"An error occurred while scraping the website: {e}"

# Specific prompt for generating Python Selenium scripts
selenium_script_prompt = """
Write a Python Selenium script that automates logging in to a website. The script should:
1. Open the website using Selenium.
2. Find the username and password fields by their CSS selectors.
3. Input a username and password.
4. Click the login button.
5. Wait for the login process to complete and verify that the user is redirected to the homepage.
"""

# Specific prompt for generating Test Cases based on the generated Selenium script
qa_test_case_prompt = """
Generate test cases based on the following Selenium script. The test cases should include:
1. Test Case Description
2. Test Steps (e.g., Open the browser, Input username and password, etc.)
3. Expected Results (e.g., User is successfully logged in and redirected to the homepage)

Selenium Script:
{selenium_script}
"""

# Define the Agent class
class Agent:
    def __init__(self, name, role):
        self.name = name
        self.role = role

    def execute_task(self, task_name, prompt=None, url=None, previous_result=None):
        """Execute a task by invoking the AI model or scraping a website."""
        st.write(f"{self.name} ({self.role}) is executing: {task_name}...")

        time.sleep(2)  # Simulate processing time

        # Use the previous result if available
        if previous_result:
            prompt = f"Use the previous result and create new content based on that: {previous_result}"

        if task_name == "Requirements Gathering" and url:
            # Use the tool to gather requirements from the website
            result = requirements_gathering_from_website(url)
        elif task_name == "Script Generation":
            # Use the specific prompt for Selenium script generation
            result = call_gemini(selenium_script_prompt)  # This is the updated prompt for script generation
        elif task_name == "Test Case Creation":
            # Use the test case generation prompt for QA
            result = call_gemini(qa_test_case_prompt.format(selenium_script=previous_result))
        else:
            # Use the AI model for other tasks
            result = call_gemini(prompt)

        return result

# Instantiate agents with their respective roles
agents = [
    Agent(name="Alice", role="Business Analyst"),
    Agent(name="Bob", role="Developer"),
    Agent(name="Charlie", role="QA Tester"),
]

# Define task prompts for each role
task_prompts = {
    "Requirements Gathering": "Generate a list of requirements to test the website",
    "User Story Creation": "Create selenium based user stories for the website based on the gathered requirements.",
    "Script Generation": "Write selenium Python scripts based on the user stories for the website functionality.",
    "Test Case Creation": "Create test cases based on the selenium scripts for the website.",
}

# Function to execute the workflow
def execute_workflow(selected_tasks, url=None):
    st.write("Starting Workflow Execution...")
    workflow_results = {}
    previous_result = None  # Start with no previous result

    # Ensure the tasks are executed in sequence
    for idx, task_name in enumerate(selected_tasks):
        # Assign the task to the appropriate agent based on the role
        agent = None
        if "Requirements" in task_name:
            agent = next(agent for agent in agents if agent.role == "Business Analyst")
        elif "User Story" in task_name:
            agent = next(agent for agent in agents if agent.role == "Business Analyst")  # Alice now creates user stories
        elif "Script" in task_name:
            agent = next(agent for agent in agents if agent.role == "Developer")
        elif "Test Case" in task_name:
            agent = next(agent for agent in agents if agent.role == "QA Tester")

        if agent:
            st.write(f"Task '{task_name}' assigned to {agent.name} ({agent.role}).")
            prompt = task_prompts.get(task_name, "Provide a default prompt for AI.")
            result = agent.execute_task(task_name, prompt=prompt, url=url if task_name == "Requirements Gathering" else None, previous_result=previous_result)
            st.success(f"{task_name} Result: {result}")
            workflow_results[task_name] = result
            previous_result = result  # Pass the result to the next agent
        else:
            st.error(f"No suitable agent found for task: {task_name}")

    st.write("Workflow Execution Completed!")
    st.subheader("Consolidated Results")
    for idx, (task_name, result) in enumerate(workflow_results.items(), start=1):
        st.write(f"{idx}. {task_name}: {result}")

# Streamlit UI
st.title("Multi-Agent Workflow Management System")

# Sidebar Navigation
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("", ["Manage Agents", "Manage Tasks", "Workflow Execution"])

# Manage Agents
if selected_page == "Manage Agents":
    st.header("Manage Agents")
    agent_name = st.text_input("Agent Name")
    agent_role = st.selectbox("Agent Role", ["Business Analyst", "Developer", "QA Tester"])

    if st.button("Add Agent"):
        if agent_name and agent_role:
            agents.append(Agent(name=agent_name, role=agent_role))
            st.success(f"Agent '{agent_name}' with role '{agent_role}' added successfully!")
        else:
            st.error("Agent name and role are required.")

    st.subheader("Existing Agents")
    for agent in agents:
        st.write(f"{agent.name} ({agent.role})")

# Manage Tasks
elif selected_page == "Manage Tasks":
    st.header("Manage Tasks")
    task_name = st.text_input("Task Name")
    task_description = st.text_area("Task Description")
    task_roles = st.multiselect("Associated Agent Roles", ["Business Analyst", "Developer", "QA Tester"])

    if st.button("Add Task"):
        if task_name:
            task_prompts[task_name] = task_description
            st.success(f"Task '{task_name}' added successfully!")
        else:
            st.error("Task name is required.")

    st.subheader("Existing Tasks")
    for task, description in task_prompts.items():
        st.write(f"**{task}**: {description}")

# Workflow Execution
elif selected_page == "Workflow Execution":
    st.header("Execute Workflow")

    # Setup the tasks
    selected_tasks = st.multiselect("Select Tasks in Sequence", list(task_prompts.keys()))
    website_url = st.text_input("Enter Website URL for Requirements Gathering")

    execute_workflow_button = st.button("Run Workflow")

    if execute_workflow_button:
        execute_workflow(selected_tasks, url=website_url if website_url else None)

