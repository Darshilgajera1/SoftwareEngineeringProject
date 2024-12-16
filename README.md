# ToolSphere

## Overview
**ToolSphere** is an innovative platform designed to empower Large Language Model (LLM) agents with the ability to create and utilize tools autonomously. The platform acts as a dynamic repository, or "Pool Of Tools" where agents can store, share, and access tools that they have created or that others have made available.

### Live Demo
Check out the live demo at [ToolSphere Live Demo](http://pooloftools.westus2.cloudapp.azure.com:443/).

### Key Features:
- **Automated Tool Creation:** When given a task by a human user, an agent will first search the "Pool Of Tools" for an existing tool that can complete the task. If no suitable tool is found, the agent will autonomously create a new tool tailored to the task at hand.
- **Collaborative Environment:** Tools created by one agent are made accessible to other agents, fostering a collaborative ecosystem where agents can learn from and build upon each other's work.
- **Efficient Task Resolution:** By leveraging existing tools in the Pool Of Tools, agents can quickly and efficiently solve user problems, reducing redundancy and maximizing resource utilization.

## How It Works
1. **User Input:** A human user provides input to an LLM agent, specifying a task or problem that needs to be solved.
2. **Tool Search:** The agent checks the Pool Of Tools to see if there is an existing tool that can be used to complete the task.
3. **Tool Utilization:** If a relevant tool is found, the agent utilizes it to complete the task.
4. **Tool Creation:** If no suitable tool exists, the agent autonomously creates a new tool, stores it in the Pool Of Tools, and then uses it to complete the task.
5. **Tool Sharing:** The newly created tool becomes available in the Pool Of Tools for other agents to use in future tasks.

## Why Pool Of Tools?
Pool Of Tools is designed to enhance the efficiency and autonomy of LLM agents by providing a shared platform for tool creation and utilization. This reduces the need for agents to repeatedly solve the same problems and allows them to focus on creating more sophisticated and innovative solutions.

## Getting Started
To get started with Pool Of Tools:
1. Clone the repository: `git clone https://github.com/your-username/pot.git`
2. Navigate to the project directory: `cd pot`
3. Install the necessary dependencies: `pip install -r requirements.txt`

## Contributing
Contributions are welcome! Whether it's adding new features, fixing bugs, or improving documentation, feel free to submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact
For any questions or suggestions, please feel free to contact me at my telegram [@darshilgajera].

---

Thank you for checking out Pool Of Tools! We hope it becomes an invaluable platform in your AI development journey.
