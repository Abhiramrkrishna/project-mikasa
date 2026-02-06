import chainlit as cl
from agents import MikasaAgent
import os

# Initialize the Agent
# We do this outside the function so the model doesn't reload on every chat message
agent = MikasaAgent()

@cl.on_chat_start
async def start():
    """
    Called when the chat session begins.
    """
    welcome_message = """**⚔️ Mikasa V2 Online.**

I am ready to secure your PhD or Full-time position.
My protocols include:
1.  **Scouting** hidden listings via Tavily.
2.  **Compliance Checks** (ECTS, Visa, Language).
3.  **Document Generation** (LaTeX Letters & Proposal Skeletons).

*To begin, give me a target. Example:*
`Find PhD positions in Physics Informed Neural Networks in Germany`
"""
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """
    Main Chat Loop
    """
    user_input = message.content.lower()
    
    # =========================================================
    # COMMAND: GENERATE LATEX COVER LETTER
    # Trigger: "latex #1", "generate letter for #2", etc.
    # =========================================================
    if ("latex" in user_input or "letter" in user_input) and "#" in user_input:
        
        # 1. Retrieve the search results from this session
        targets = cl.user_session.get("targets")
        
        if not targets:
            await cl.Message(content="❌ No active mission. Please search for jobs first.").send()
            return

        try:
            # Parse the index (e.g., "#1" -> index 0)
            # Looks for the number immediately following '#'
            import re
            match = re.search(r"#(\d+)", message.content)
            if not match:
                raise ValueError("No number found")
            
            idx = int(match.group(1)) - 1
            
            # Boundary check
            if idx < 0 or idx >= len(targets):
                await cl.Message(content=f"⚠️ Invalid target number. You have {len(targets)} targets.").send()
                return

            target_job = targets[idx]
            
            # 2. Notify User
            msg = cl.Message(content=f"✍️ **Drafting LaTeX Cover Letter for: {target_job['title']}**...")
            await msg.send()
            
            # 3. Call Agent to Generate LaTeX content
            latex_code = agent.generate_latex_letter(target_job)
            
            # 4. Save to a temporary file
            # We use the job title in the filename for organization
            safe_title = "".join([c for c in target_job['title'] if c.isalnum() or c==' ']).strip().replace(" ", "_")[:20]
            filename = f"CoverLetter_{safe_title}.tex"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(latex_code)
                
            # 5. Create Download Element
            elements = [
                cl.File(
                    name=filename,
                    path=filename,
                    display="inline"
                )
            ]
            
            # 6. Send Response
            await cl.Message(
                content=f"✅ **LaTeX Generated.**\n\nDownload the file below. You can upload this directly to Overleaf to compile it with your signature.",
                elements=elements
            ).send()
            return

        except Exception as e:
            await cl.Message(content=f"⚠️ Error parsing command: {str(e)}. Try: 'Generate LaTeX for #1'").send()
            return

    # =========================================================
    # COMMAND: GENERATE PROPOSAL SKELETON
    # Trigger: "proposal #1", "research plan for #2"
    # =========================================================
    if "proposal" in user_input and "#" in user_input:
        targets = cl.user_session.get("targets")
        
        if not targets:
            await cl.Message(content="❌ No active mission.").send()
            return
            
        try:
            import re
            match = re.search(r"#(\d+)", message.content)
            idx = int(match.group(1)) - 1
            target_job = targets[idx]
            
            msg = cl.Message(content=f"🧪 **Drafting Research Proposal Strategy for: {target_job['title']}**...")
            await msg.send()
            
            proposal_text = agent.generate_proposal_skeleton(target_job)
            
            await cl.Message(content=proposal_text).send()
            return
            
        except Exception as e:
            await cl.Message(content="⚠️ Error. Try: 'Generate Proposal for #1'.").send()
            return

    # =========================================================
    # COMMAND: DEFAULT (SEARCH MISSION)
    # Trigger: Anything else (e.g. "Find jobs...")
    # =========================================================
    
    # 1. Notify User of Scouting
    msg = cl.Message(content="🕵️‍♀️ **Scouting Sector & Analyzing Compliance...** (This may take 30s)")
    await msg.send()
    
    # 2. Run the Agent Mission
    # This calls the Agent -> Scout -> Search -> Analyze loop
    targets = agent.start_mission(message.content)
    
    # 3. Store results in Session (So we can refer to them later)
    cl.user_session.set("targets", targets)
    
    # 4. Update Status
    msg.content = f"✅ **Analysis Complete.** Found {len(targets)} targets."
    await msg.update()

    # 5. Render Cards
    if not targets:
        await cl.Message(content="❌ No relevant positions found. Try broadening your search terms.").send()
        return

    for i, t in enumerate(targets):
        
        # Color Coding based on Score
        score = t.get('score', 0)
        color_icon = "🟢" if score >= 85 else "🟡" if score >= 70 else "🔴"
        
        # Format Red Flags (Crucial for Compliance)
        flags = t.get('red_flags', [])
        if flags:
            flag_str = "\n".join([f"> 🚩 **{f}**" for f in flags])
        else:
            flag_str = "> ✅ No major red flags detected."
            
        # Format Checklist
        requirements = t.get('requirements_checklist', [])
        if requirements:
            checklist_str = "\n".join([f"- [ ] {req}" for req in requirements])
        else:
            checklist_str = "- [ ] Check job posting for specific docs."

        # Send the Card
        await cl.Message(
            content=f"""
### {color_icon} Target #{i+1}: {t['title']}
**Score:** {score}/100 | **Uni:** {t.get('university', 'Unknown')}
**Link:** [Open Posting]({t['url']})

**⚠️ Compliance Report:**
{flag_str}

**📋 Document Checklist:**
{checklist_str}

**⚔️ Strategy:**
{t.get('winning_factor', 'N/A')}

---
*Next Steps:*
* `Generate LaTeX for #{i+1}`
* `Generate Proposal for #{i+1}`
            """
        ).send()