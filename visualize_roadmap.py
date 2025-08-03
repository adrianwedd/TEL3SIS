#!/usr/bin/env python3
"""
TEL3SIS Roadmap Visualization Generator
Creates interactive Gantt charts and timeline visualizations from the roadmap data.
"""

import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

# Roadmap data structure
ROADMAP_DATA = {
    "phases": [
        {
            "name": "Security & Safety Foundation",
            "phase": 1,
            "quarter": "Q4 2025",
            "timeline_weeks": 6,
            "priority": "CRITICAL",
            "issues": ["#442", "#437", "#445", "#455"],
            "category": "Security",
            "color": "#FF4444"
        },
        {
            "name": "Core Agent Intelligence", 
            "phase": 2,
            "quarter": "Q4 2025",
            "timeline_weeks": 8,
            "priority": "HIGH",
            "issues": ["#454", "#453", "#436", "#439"],
            "category": "Agent Logic",
            "color": "#4444FF"
        },
        {
            "name": "Admin Infrastructure",
            "phase": 3,
            "quarter": "Q4 2025", 
            "timeline_weeks": 5,
            "priority": "HIGH",
            "issues": ["#438", "#441", "#451"],
            "category": "Infrastructure",
            "color": "#44FF44"
        },
        {
            "name": "Tool Ecosystem Expansion",
            "phase": 4,
            "quarter": "Q1 2026",
            "timeline_weeks": 8,
            "priority": "MEDIUM",
            "issues": ["#433", "#459", "#423", "#355"],
            "category": "Tools",
            "color": "#FF8844"
        },
        {
            "name": "Infrastructure & Observability",
            "phase": 5,
            "quarter": "Q1 2026",
            "timeline_weeks": 6,
            "priority": "HIGH",
            "issues": ["#463", "#440", "#418", "#447"],
            "category": "Infrastructure", 
            "color": "#8844FF"
        },
        {
            "name": "Advanced Agent Features",
            "phase": 6,
            "quarter": "Q1 2026",
            "timeline_weeks": 8,
            "priority": "MEDIUM",
            "issues": ["#372", "#426", "#420", "#369"],
            "category": "Agent Logic",
            "color": "#44FFFF"
        },
        {
            "name": "Enhanced UI/UX",
            "phase": 7,
            "quarter": "Q2 2026",
            "timeline_weeks": 10,
            "priority": "MEDIUM",
            "issues": ["#412", "#446", "#421", "#305"],
            "category": "UI/UX",
            "color": "#FF44FF"
        },
        {
            "name": "Integration & Workflow",
            "phase": 8,
            "quarter": "Q2 2026",
            "timeline_weeks": 8,
            "priority": "MEDIUM", 
            "issues": ["#430", "#411", "#400", "#395"],
            "category": "Integration",
            "color": "#FFFF44"
        },
        {
            "name": "Documentation Excellence",
            "phase": 9,
            "quarter": "Q2 2026",
            "timeline_weeks": 6,
            "priority": "LOW",
            "issues": ["#464", "#449", "#444", "#398"],
            "category": "Documentation",
            "color": "#888888"
        },
        {
            "name": "Scalability & Performance",
            "phase": 10,
            "quarter": "Q3 2026",
            "timeline_weeks": 12,
            "priority": "HIGH",
            "issues": ["#401", "#410", "#361", "#334"],
            "category": "Scalability", 
            "color": "#FF8888"
        },
        {
            "name": "Advanced Features & Testing",
            "phase": 11,
            "quarter": "Q3 2026",
            "timeline_weeks": 8,
            "priority": "MEDIUM",
            "issues": ["#461", "#452", "#390", "#326"],
            "category": "Testing",
            "color": "#88FF88"
        }
    ]
}

def create_gantt_chart():
    """Create an interactive Gantt chart visualization"""
    
    # Convert phases to DataFrame
    df_data = []
    start_date = datetime(2025, 10, 1)  # Q4 2025 start
    current_date = start_date
    
    for phase in ROADMAP_DATA["phases"]:
        end_date = current_date + timedelta(weeks=phase["timeline_weeks"])
        
        df_data.append({
            "Phase": f"Phase {phase['phase']}: {phase['name']}",
            "Start": current_date,
            "End": end_date,
            "Duration": phase["timeline_weeks"],
            "Priority": phase["priority"],
            "Category": phase["category"],
            "Issues": len(phase["issues"]),
            "Color": phase["color"],
            "Quarter": phase["quarter"]
        })
        
        # Overlap some phases for parallel development
        if phase["phase"] in [1, 4, 7, 10]:  # Start new quarter
            current_date = end_date
        else:
            current_date = current_date + timedelta(weeks=2)  # Slight overlap
    
    df = pd.DataFrame(df_data)
    
    # Create Gantt chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End", 
        y="Phase",
        color="Priority",
        title="🗺️ TEL3SIS Development Roadmap - Interactive Timeline",
        color_discrete_map={
            "CRITICAL": "#FF4444",
            "HIGH": "#FF8844", 
            "MEDIUM": "#44FF44",
            "LOW": "#888888"
        },
        hover_data=["Duration", "Issues", "Category", "Quarter"]
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_x=0.5,
        xaxis_title="Timeline",
        yaxis_title="Development Phases",
        font=dict(size=12)
    )
    
    return fig

def create_dependency_graph():
    """Create a network graph showing phase dependencies"""
    
    G = nx.DiGraph()
    
    # Add nodes (phases)
    for phase in ROADMAP_DATA["phases"]:
        G.add_node(
            phase["phase"],
            name=phase["name"],
            priority=phase["priority"],
            category=phase["category"],
            issues=len(phase["issues"])
        )
    
    # Add edges (dependencies) - simplified logical flow
    dependencies = [
        (1, 2), (1, 3),  # Security foundation enables agent & admin
        (2, 6), (3, 7),  # Agent logic → Advanced features, Admin → UI/UX
        (4, 8),          # Tools → Integration
        (5, 10),         # Infrastructure → Scalability
        (6, 11), (7, 8), # Advanced features → Testing, UI/UX → Integration
        (9, 11),         # Documentation → Testing (parallel)
        (10, 11)         # Scalability → Testing
    ]
    
    G.add_edges_from(dependencies)
    
    # Create visualization
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Color nodes by priority
    priority_colors = {
        "CRITICAL": "#FF4444",
        "HIGH": "#FF8844",
        "MEDIUM": "#44FF44", 
        "LOW": "#888888"
    }
    
    node_colors = [priority_colors[G.nodes[node]["priority"]] for node in G.nodes()]
    node_sizes = [G.nodes[node]["issues"] * 200 + 500 for node in G.nodes()]
    
    # Draw network
    nx.draw(
        G, pos,
        node_color=node_colors,
        node_size=node_sizes,
        with_labels=True,
        labels={node: f"P{node}\n{G.nodes[node]['name'][:20]}..." 
                for node in G.nodes()},
        font_size=8,
        font_weight='bold',
        arrows=True,
        arrowsize=20,
        edge_color='gray',
        alpha=0.8
    )
    
    plt.title("🔗 TEL3SIS Phase Dependencies Network", size=16, weight='bold')
    plt.axis('off')
    
    # Add legend
    for priority, color in priority_colors.items():
        plt.scatter([], [], c=color, alpha=0.8, s=100, label=priority)
    plt.legend(title="Priority Level", loc='upper right')
    
    return plt

def create_category_breakdown():
    """Create a category breakdown visualization"""
    
    # Aggregate data by category
    category_data = {}
    for phase in ROADMAP_DATA["phases"]:
        cat = phase["category"]
        if cat not in category_data:
            category_data[cat] = {"phases": 0, "weeks": 0, "issues": 0}
        
        category_data[cat]["phases"] += 1
        category_data[cat]["weeks"] += phase["timeline_weeks"]
        category_data[cat]["issues"] += len(phase["issues"])
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Issues by Category", "Timeline by Category", 
                       "Phases by Category", "Priority Distribution"),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "pie"}]]
    )
    
    categories = list(category_data.keys())
    colors = px.colors.qualitative.Set3[:len(categories)]
    
    # Issues pie chart
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=[category_data[cat]["issues"] for cat in categories],
            name="Issues",
            marker_colors=colors
        ),
        row=1, col=1
    )
    
    # Timeline bar chart
    fig.add_trace(
        go.Bar(
            x=categories,
            y=[category_data[cat]["weeks"] for cat in categories],
            name="Weeks",
            marker_color=colors
        ),
        row=1, col=2
    )
    
    # Phases bar chart  
    fig.add_trace(
        go.Bar(
            x=categories,
            y=[category_data[cat]["phases"] for cat in categories],
            name="Phases",
            marker_color=colors
        ),
        row=2, col=1
    )
    
    # Priority distribution
    priority_counts = {}
    for phase in ROADMAP_DATA["phases"]:
        priority = phase["priority"]
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    fig.add_trace(
        go.Pie(
            labels=list(priority_counts.keys()),
            values=list(priority_counts.values()),
            name="Priority"
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        title_text="📊 TEL3SIS Roadmap Analytics Dashboard",
        title_x=0.5
    )
    
    return fig

def generate_mermaid_diagram():
    """Generate Mermaid diagram code for GitHub/GitLab rendering"""
    
    mermaid_code = """
    ```mermaid
    gantt
        title TEL3SIS Development Roadmap
        dateFormat  YYYY-MM-DD
        section Critical Path
        Security & Safety Foundation    :crit, phase1, 2025-10-01, 6w
        Core Agent Intelligence         :crit, phase2, after phase1, 8w
        Admin Infrastructure           :phase3, after phase1, 5w
        
        section Platform Enhancement  
        Tool Ecosystem Expansion      :phase4, 2026-01-01, 8w
        Infrastructure & Observability :phase5, after phase4, 6w
        Advanced Agent Features        :phase6, after phase4, 8w
        
        section User Experience
        Enhanced UI/UX                 :phase7, 2026-04-01, 10w  
        Integration & Workflow         :phase8, after phase7, 8w
        Documentation Excellence       :phase9, after phase7, 6w
        
        section Scalability
        Scalability & Performance      :phase10, 2026-07-01, 12w
        Advanced Features & Testing    :phase11, after phase10, 8w
    ```
    
    ```mermaid
    graph TD
        A[Phase 1: Security & Safety] --> B[Phase 2: Agent Intelligence]
        A --> C[Phase 3: Admin Infrastructure]
        B --> F[Phase 6: Advanced Agent Features]
        C --> G[Phase 7: Enhanced UI/UX]
        D[Phase 4: Tool Expansion] --> H[Phase 8: Integration]
        E[Phase 5: Infrastructure] --> J[Phase 10: Scalability]
        F --> K[Phase 11: Testing]
        G --> H
        I[Phase 9: Documentation] --> K
        J --> K
        
        classDef critical fill:#ff4444,stroke:#333,stroke-width:3px
        classDef high fill:#ff8844,stroke:#333,stroke-width:2px  
        classDef medium fill:#44ff44,stroke:#333,stroke-width:1px
        
        class A critical
        class B,C,E,J high
        class D,F,G,H,K medium
        class I low
    ```
    """
    
    return mermaid_code

def main():
    """Generate all visualizations"""
    
    print("🎨 Generating TEL3SIS Roadmap Visualizations...")
    
    # 1. Interactive Gantt Chart
    print("📊 Creating Interactive Gantt Chart...")
    gantt_fig = create_gantt_chart()
    gantt_fig.write_html("tel3sis_roadmap_gantt.html")
    gantt_fig.show()
    
    # 2. Dependency Network Graph
    print("🔗 Creating Dependency Network Graph...")
    plt_fig = create_dependency_graph()
    plt_fig.savefig("tel3sis_roadmap_network.png", dpi=300, bbox_inches='tight')
    plt_fig.show()
    
    # 3. Category Analytics Dashboard
    print("📈 Creating Analytics Dashboard...")
    analytics_fig = create_category_breakdown()
    analytics_fig.write_html("tel3sis_roadmap_analytics.html")
    analytics_fig.show()
    
    # 4. Mermaid Diagram Code
    print("🏗️ Generating Mermaid Diagram Code...")
    mermaid_code = generate_mermaid_diagram()
    with open("tel3sis_roadmap_mermaid.md", "w") as f:
        f.write("# TEL3SIS Roadmap - Mermaid Diagrams\n\n")
        f.write(mermaid_code)
    
    print("✅ All visualizations generated!")
    print("\nFiles created:")
    print("- tel3sis_roadmap_gantt.html (Interactive Gantt Chart)")
    print("- tel3sis_roadmap_network.png (Dependency Network)")
    print("- tel3sis_roadmap_analytics.html (Analytics Dashboard)")
    print("- tel3sis_roadmap_mermaid.md (Mermaid Diagrams for GitHub)")

if __name__ == "__main__":
    main()