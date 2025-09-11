# energy_visualizer.py - Integration module for plots and cartoons
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnergyVisualizer:
    """
    Clean visualization generator for Swiss energy scenarios
    Integrates with existing chatbot architecture
    """

    def __init__(self):
        # Dark2 color palette for professional look
        self.colors = {
            "ZERO": "#1b9e77",  # Teal
            "WWB": "#d95f02",  # Orange
            "DIVERGENZ": "#7570b3",  # Purple
            "ZERO_A": "#e7298a",  # Pink
            "ZERO_B": "#66a61e",  # Green
            "ZERO_C": "#e6ab02",  # Yellow
        }

        self.energy_colors = {
            "Solar": "#ffd700",  # Gold
            "Hydro": "#0066cc",  # Blue
            "Wind": "#87ceeb",  # Sky blue
            "Nuclear": "#ff6600",  # Orange
            "Biomass": "#228b22",  # Forest green
            "Gas": "#8b4513",  # Brown
            "Geothermal": "#a0522d",  # Sienna
        }

        # Clean ggplot2-inspired layout
        self.base_layout = {
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"family": "Arial, sans-serif", "size": 12, "color": "#2c2c2c"},
            "margin": {"t": 60, "r": 30, "b": 60, "l": 60},
            "showlegend": True,
            "legend": {
                "x": 1,
                "y": 1,
                "xanchor": "right",
                "yanchor": "top",
                "bgcolor": "rgba(255,255,255,0.9)",
                "bordercolor": "#e5e5e5",
                "borderwidth": 1,
            },
        }

        self.clean_axis = {
            "showgrid": True,
            "gridcolor": "#f0f0f0",
            "gridwidth": 1,
            "zeroline": False,
            "showline": True,
            "linecolor": "#d1d5db",
            "linewidth": 1,
            "ticks": "outside",
            "tickcolor": "#d1d5db",
            "tickfont": {"size": 11, "color": "#666"},
            "title": {"font": {"size": 12, "color": "#333"}},
        }

    def create_visualization(
        self, data: pd.DataFrame, query: str, chart_type: str = "auto"
    ) -> Optional[go.Figure]:
        """
        Main method to create appropriate visualization

        Args:
            data: DataFrame with energy scenario data
            query: User query string
            chart_type: Specific chart type or 'auto' for intelligent selection

        Returns:
            Plotly figure or None if no suitable visualization
        """
        try:
            if data.empty:
                logger.warning("Empty dataset provided")
                return self._create_placeholder_plot(query)

            # Auto-detect chart type if not specified
            if chart_type == "auto":
                chart_type = self._detect_chart_type(data, query)

            # Route to appropriate visualization method
            viz_methods = {
                "cleveland": self._create_cleveland_plot,
                "bar": self._create_bar_plot,
                "line": self._create_line_plot,
                "area": self._create_area_plot,
                "stacked_bar": self._create_stacked_bar,
                "heatmap": self._create_heatmap,
                "pie": self._create_pie_plot,
            }

            if chart_type in viz_methods:
                return viz_methods[chart_type](data, query)
            else:
                logger.warning(f"Unknown chart type: {chart_type}")
                return self._create_bar_plot(data, query)

        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return self._create_error_plot(str(e))

    def _detect_chart_type(self, data: pd.DataFrame, query: str) -> str:
        """Intelligently detect appropriate chart type"""

        # Count categorical columns
        categorical_cols = data.select_dtypes(include=["object", "category"]).columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns

        # Check for scenario/category column
        scenario_col = None
        for col in categorical_cols:
            if any(
                keyword in col.lower()
                for keyword in ["scenario", "energy_source", "technology"]
            ):
                scenario_col = col
                break

        if scenario_col is not None:
            unique_categories = data[scenario_col].nunique()

            # Use Cleveland plot only when >4 categories
            if unique_categories > 4:
                return "cleveland"
            else:
                return "bar"

        # Check for time series data
        if "year" in data.columns or any("time" in col.lower() for col in data.columns):
            if "emission" in query.lower() or "trend" in query.lower():
                return "area"
            else:
                return "line"

        # Check for composition queries
        if any(
            word in query.lower()
            for word in ["mix", "composition", "breakdown", "share"]
        ):
            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                return "pie"

        # Check for comparison queries
        if any(word in query.lower() for word in ["compare", "comparison", "versus"]):
            return "bar"

        # Default fallback
        return "bar"

    def _create_cleveland_plot(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create Cleveland dot plot for many categories"""

        # Find categorical and numeric columns
        cat_col = data.select_dtypes(include=["object"]).columns[0]
        num_col = data.select_dtypes(include=[np.number]).columns[0]

        # Group and sort data
        grouped_data = data.groupby(cat_col)[num_col].mean().reset_index()
        grouped_data = grouped_data.sort_values(num_col, ascending=True)

        fig = go.Figure()

        # Add dots
        fig.add_trace(
            go.Scatter(
                x=grouped_data[num_col],
                y=grouped_data[cat_col],
                mode="markers",
                marker=dict(
                    size=12,
                    color=self.colors["ZERO"],
                    line=dict(width=2, color="white"),
                ),
                hovertemplate=f"<b>%{{y}}</b><br>{num_col}: %{{x}}<extra></extra>",
                showlegend=False,
            )
        )

        # Add reference lines
        for i, (_, row) in enumerate(grouped_data.iterrows()):
            fig.add_shape(
                type="line",
                x0=0,
                x1=row[num_col],
                y0=i,
                y1=i,
                line=dict(color="#e5e5e5", width=1),
            )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": f"{num_col} by {cat_col}", "x": 0},
                "xaxis": {**self.clean_axis, "title": num_col},
                "yaxis": {**self.clean_axis, "title": "", "showgrid": False},
                "height": max(400, len(grouped_data) * 25),  # Dynamic height
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_bar_plot(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create clean bar plot for ≤4 categories"""

        cat_col = data.select_dtypes(include=["object"]).columns[0]
        num_col = data.select_dtypes(include=[np.number]).columns[0]

        # Group data
        grouped_data = data.groupby(cat_col)[num_col].mean().reset_index()

        # Get colors based on category names
        colors = [
            self.colors.get(cat, self.colors["ZERO"]) for cat in grouped_data[cat_col]
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=grouped_data[cat_col],
                y=grouped_data[num_col],
                marker=dict(color=colors, line=dict(width=1, color="white")),
                width=0.6,  # Slim bars
                hovertemplate=f"<b>%{{x}}</b><br>{num_col}: %{{y}}<extra></extra>",
                showlegend=False,
            )
        )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": f"{num_col} by {cat_col}", "x": 0},
                "xaxis": {**self.clean_axis, "title": cat_col},
                "yaxis": {**self.clean_axis, "title": num_col},
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_line_plot(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create time series line plot"""

        fig = go.Figure()

        # Find time column
        time_col = "year" if "year" in data.columns else data.columns[0]

        # Find scenario column
        scenario_col = None
        for col in data.columns:
            if "scenario" in col.lower():
                scenario_col = col
                break

        numeric_cols = data.select_dtypes(include=[np.number]).columns
        value_col = [col for col in numeric_cols if col != time_col][0]

        if scenario_col:
            # Multiple lines for scenarios
            for i, scenario in enumerate(data[scenario_col].unique()):
                scenario_data = data[data[scenario_col] == scenario]

                fig.add_trace(
                    go.Scatter(
                        x=scenario_data[time_col],
                        y=scenario_data[value_col],
                        mode="lines+markers",
                        name=scenario,
                        line=dict(
                            color=self.colors.get(
                                scenario, list(self.colors.values())[i]
                            ),
                            width=2.5,
                        ),
                        marker=dict(size=6),
                        hovertemplate=f"<b>%{{fullData.name}}</b><br>{time_col}: %{{x}}<br>{value_col}: %{{y}}<extra></extra>",
                    )
                )
        else:
            # Single line
            fig.add_trace(
                go.Scatter(
                    x=data[time_col],
                    y=data[value_col],
                    mode="lines+markers",
                    line=dict(color=self.colors["ZERO"], width=2.5),
                    marker=dict(size=6),
                    showlegend=False,
                )
            )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": f"{value_col} Over Time", "x": 0},
                "xaxis": {**self.clean_axis, "title": time_col},
                "yaxis": {**self.clean_axis, "title": value_col},
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_area_plot(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create area plot for emissions/trends"""

        fig = go.Figure()

        time_col = "year" if "year" in data.columns else data.columns[0]
        scenario_col = None
        for col in data.columns:
            if "scenario" in col.lower():
                scenario_col = col
                break

        numeric_cols = data.select_dtypes(include=[np.number]).columns
        value_col = [col for col in numeric_cols if col != time_col][0]

        if scenario_col:
            for i, scenario in enumerate(data[scenario_col].unique()):
                scenario_data = data[data[scenario_col] == scenario]

                fig.add_trace(
                    go.Scatter(
                        x=scenario_data[time_col],
                        y=scenario_data[value_col],
                        mode="lines",
                        name=scenario,
                        fill="tonexty" if i > 0 else "tozeroy",
                        line=dict(
                            color=self.colors.get(
                                scenario, list(self.colors.values())[i]
                            ),
                            width=2,
                        ),
                        fillcolor=self.colors.get(
                            scenario, list(self.colors.values())[i]
                        )
                        + "20",
                    )
                )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": f"{value_col} Pathways", "x": 0},
                "xaxis": {**self.clean_axis, "title": time_col},
                "yaxis": {**self.clean_axis, "title": value_col},
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_stacked_bar(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create stacked bar chart for energy mix"""

        fig = go.Figure()

        # Assume data has scenarios as rows and energy sources as columns
        if "scenario" in data.columns:
            scenario_col = "scenario"
            energy_cols = [col for col in data.columns if col != scenario_col]

            for i, energy_source in enumerate(energy_cols):
                fig.add_trace(
                    go.Bar(
                        x=data[scenario_col],
                        y=data[energy_source],
                        name=energy_source,
                        marker=dict(
                            color=self.energy_colors.get(
                                energy_source, list(self.energy_colors.values())[i]
                            )
                        ),
                    )
                )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": "Energy Mix by Scenario", "x": 0},
                "xaxis": {**self.clean_axis, "title": "Scenario"},
                "yaxis": {**self.clean_axis, "title": "Energy Production (TWh)"},
                "barmode": "stack",
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_pie_plot(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create pie chart for composition"""

        # Find categorical and numeric columns
        cat_col = data.select_dtypes(include=["object"]).columns[0]
        num_col = data.select_dtypes(include=[np.number]).columns[0]

        # Group data
        pie_data = data.groupby(cat_col)[num_col].sum().reset_index()

        fig = go.Figure()

        fig.add_trace(
            go.Pie(
                labels=pie_data[cat_col],
                values=pie_data[num_col],
                hole=0.3,
                marker=dict(
                    colors=[
                        self.energy_colors.get(label, self.colors["ZERO"])
                        for label in pie_data[cat_col]
                    ],
                    line=dict(color="white", width=2),
                ),
                textfont=dict(size=12),
                hovertemplate="<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        )

        layout = self.base_layout.copy()
        layout.update(
            {"title": {"text": f"{num_col} Composition", "x": 0.5}, "showlegend": True}
        )

        fig.update_layout(layout)
        return fig

    def _create_heatmap(self, data: pd.DataFrame, query: str) -> go.Figure:
        """Create correlation heatmap"""

        # Calculate correlation matrix for numeric columns
        numeric_data = data.select_dtypes(include=[np.number])
        corr_matrix = numeric_data.corr()

        fig = go.Figure()

        fig.add_trace(
            go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale=[[0, "#d95f02"], [0.5, "#ffffff"], [1, "#1b9e77"]],
                zmin=-1,
                zmax=1,
                text=corr_matrix.round(2).values,
                texttemplate="%{text}",
                textfont=dict(size=11),
                hovertemplate="<b>%{y} vs %{x}</b><br>Correlation: %{z}<extra></extra>",
            )
        )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": "Correlation Matrix", "x": 0},
                "xaxis": {**self.clean_axis, "showgrid": False},
                "yaxis": {
                    **self.clean_axis,
                    "showgrid": False,
                    "autorange": "reversed",
                },
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_placeholder_plot(self, query: str) -> go.Figure:
        """Create placeholder when no data available"""

        fig = go.Figure()

        fig.add_annotation(
            text="📊 Visualization will appear here<br>when relevant data is available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666"),
        )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": "Data Visualization", "x": 0},
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
            }
        )

        fig.update_layout(layout)
        return fig

    def _create_error_plot(self, error_msg: str) -> go.Figure:
        """Create error visualization"""

        fig = go.Figure()

        fig.add_annotation(
            text=f"⚠️ Visualization Error<br>{error_msg}",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#e74c3c"),
        )

        layout = self.base_layout.copy()
        layout.update(
            {
                "title": {"text": "Visualization Error", "x": 0},
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
            }
        )

        fig.update_layout(layout)
        return fig


class EnergyCartoonGenerator:
    """
    Cartoon script generator for Swiss energy scenarios
    Creates character-based explanations
    """

    def __init__(self):
        self.characters = {
            "solar": {
                "name": "Solar Sam",
                "emoji": "☀️",
                "personality": "Optimistic, energetic, growth-focused",
                "expertise": "Solar energy, renewable expansion, distributed generation",
            },
            "hydro": {
                "name": "Hydro Hannah",
                "emoji": "💧",
                "personality": "Reliable, steady, Swiss heritage proud",
                "expertise": "Hydroelectric power, seasonal storage, Swiss backbone",
            },
            "nuclear": {
                "name": "Nuclear Nora",
                "emoji": "⚛️",
                "personality": "Safety-focused, concerned about phase-out",
                "expertise": "Nuclear power, baseload electricity, transition challenges",
            },
            "citizen": {
                "name": "Swiss Clara",
                "emoji": "🇨🇭",
                "personality": "Practical, cost-conscious, reliability-focused",
                "expertise": "Consumer perspective, daily life impact, energy bills",
            },
            "expert": {
                "name": "Dr. Energy",
                "emoji": "👨‍🔬",
                "personality": "Analytical, data-driven, technical",
                "expertise": "Energy policy, statistics, scenario modeling",
            },
        }

    def generate_cartoon_script(
        self, query: str, data: pd.DataFrame, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate cartoon script based on query and data

        Args:
            query: User question
            data: Energy scenario data
            context: Additional context (scenario type, complexity, etc.)

        Returns:
            Dictionary with script, characters, and metadata
        """

        # Determine script type based on query
        script_type = self._classify_query_type(query)

        # Select appropriate characters
        characters = self._select_characters(script_type, query)

        # Generate dialogue
        dialogue = self._generate_dialogue(script_type, query, data, characters)

        return {
            "script_type": script_type,
            "characters": characters,
            "dialogue": dialogue,
            "setting": self._get_setting(script_type),
            "duration_estimate": f"{len(dialogue) * 30} seconds",
            "complexity": context.get("complexity", "intermediate"),
        }

    def _classify_query_type(self, query: str) -> str:
        """Classify query to determine script type"""

        query_lower = query.lower()

        if any(word in query_lower for word in ["compare", "versus", "difference"]):
            return "comparison"
        elif any(
            word in query_lower for word in ["future", "trend", "growth", "evolution"]
        ):
            return "future_vision"
        elif any(word in query_lower for word in ["challenge", "problem", "difficult"]):
            return "problem_solving"
        elif any(word in query_lower for word in ["cost", "investment", "money"]):
            return "economics"
        elif any(word in query_lower for word in ["winter", "seasonal", "storage"]):
            return "technical_challenge"
        else:
            return "explanation"

    def _select_characters(self, script_type: str, query: str) -> List[str]:
        """Select appropriate characters for the script"""

        # Base character selection logic
        character_sets = {
            "comparison": ["solar", "nuclear", "expert"],
            "future_vision": ["solar", "citizen", "expert"],
            "problem_solving": ["hydro", "nuclear", "expert"],
            "economics": ["citizen", "expert"],
            "technical_challenge": ["solar", "hydro", "expert"],
            "explanation": ["expert", "citizen"],
        }

        # Add query-specific characters
        selected = character_sets.get(script_type, ["expert", "citizen"])

        if "solar" in query.lower() and "solar" not in selected:
            selected.append("solar")
        if "nuclear" in query.lower() and "nuclear" not in selected:
            selected.append("nuclear")

        return selected[:3]  # Limit to 3 characters for clarity

    def _generate_dialogue(
        self, script_type: str, query: str, data: pd.DataFrame, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Generate dialogue based on script type and characters"""

        # Extract key data points for the conversation
        data_insights = self._extract_data_insights(data)

        # Script templates
        templates = {
            "comparison": self._create_comparison_dialogue,
            "future_vision": self._create_future_dialogue,
            "problem_solving": self._create_problem_dialogue,
            "economics": self._create_economics_dialogue,
            "technical_challenge": self._create_technical_dialogue,
            "explanation": self._create_explanation_dialogue,
        }

        generator = templates.get(script_type, self._create_explanation_dialogue)
        return generator(query, data_insights, characters)

    def _extract_data_insights(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extract key insights from data for dialogue"""

        insights = {"has_data": not data.empty}

        if data.empty:
            return insights

        # Look for key columns and extract insights
        numeric_cols = data.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            main_col = numeric_cols[0]
            insights.update(
                {
                    "main_metric": main_col,
                    "max_value": data[main_col].max(),
                    "min_value": data[main_col].min(),
                    "has_scenarios": "scenario" in data.columns,
                    "has_time_data": "year" in data.columns,
                }
            )

            if "scenario" in data.columns:
                scenario_stats = data.groupby("scenario")[main_col].mean()
                insights["scenario_comparison"] = scenario_stats.to_dict()

        return insights

    def _create_comparison_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create comparison dialogue"""

        dialogue = [
            {
                "character": characters[0],
                "type": "speech",
                "text": f"Let's compare the different approaches to {query}. Each scenario represents a different path for Switzerland's energy future.",
            },
            {
                "character": characters[1] if len(characters) > 1 else characters[0],
                "type": "speech",
                "text": "The key differences lie in the speed of transition and technology mix. Some prioritize rapid change, others focus on gradual, reliable transformation.",
            },
        ]

        if insights.get("scenario_comparison"):
            dialogue.append(
                {
                    "character": characters[-1],
                    "type": "speech",
                    "text": f"Looking at the data, we can see clear differences between scenarios in terms of {insights.get('main_metric', 'energy production')}.",
                }
            )

        return dialogue

    def _create_future_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create future vision dialogue"""

        return [
            {
                "character": characters[0],
                "type": "speech",
                "text": "Picture Switzerland in 2050 - a completely transformed energy landscape powered by clean, renewable sources.",
            },
            {
                "character": characters[1] if len(characters) > 1 else characters[0],
                "type": "thought",
                "text": "But how do we get there? The transition requires careful planning and massive investment in new technologies.",
            },
        ]

    def _create_problem_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create problem-solving dialogue"""

        return [
            {
                "character": characters[0],
                "type": "speech",
                "text": f"The challenge you're asking about - {query} - is one of the key issues we face in the energy transition.",
            },
            {
                "character": characters[-1],
                "type": "speech",
                "text": "Every challenge has solutions, but they require trade-offs between cost, speed, and reliability. Let's explore the options.",
            },
        ]

    def _create_economics_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create economics-focused dialogue"""

        return [
            {
                "character": "citizen",
                "type": "speech",
                "text": "What I really want to know is: how will this affect my energy bills and the Swiss economy?",
            },
            {
                "character": "expert",
                "type": "speech",
                "text": "Great question! The economics involve upfront investments but long-term savings through energy independence and lower operational costs.",
            },
        ]

    def _create_technical_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create technical challenge dialogue"""

        return [
            {
                "character": characters[0],
                "type": "speech",
                "text": f"The technical aspects of {query} require us to balance multiple factors: reliability, efficiency, and scalability.",
            },
            {
                "character": characters[-1],
                "type": "speech",
                "text": "Swiss engineering excellence will be crucial in solving these technical challenges while maintaining our high standards for energy security.",
            },
        ]

    def _create_explanation_dialogue(
        self, query: str, insights: Dict, characters: List[str]
    ) -> List[Dict[str, str]]:
        """Create general explanation dialogue"""

        return [
            {
                "character": "expert",
                "type": "speech",
                "text": f"To answer your question about {query}, let me break down the key concepts and data behind Switzerland's energy scenarios.",
            },
            {
                "character": "citizen",
                "type": "speech",
                "text": "Please explain it in simple terms - how does this affect everyday Swiss life and our energy future?",
            },
        ]

    def _get_setting(self, script_type: str) -> str:
        """Get appropriate setting for script type"""

        settings = {
            "comparison": "Swiss Federal Energy Council meeting room",
            "future_vision": "Mountaintop overlooking renewable energy installations",
            "problem_solving": "Swiss energy crisis management center",
            "economics": "Swiss family kitchen table",
            "technical_challenge": "Swiss energy research laboratory",
            "explanation": "Swiss energy information center",
        }

        return settings.get(script_type, "Swiss energy conference room")


# Integration functions for your chatbot
def integrate_visualization(
    data: pd.DataFrame, query: str, response_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main integration function for your chatbot

    Args:
        data: DataFrame from your data extraction pipeline
        query: User's question
        response_context: Context from your LLM response

    Returns:
        Dictionary with visualization and cartoon components
    """

    visualizer = EnergyVisualizer()
    cartoon_gen = EnergyCartoonGenerator()

    # Create visualization
    try:
        fig = visualizer.create_visualization(data, query)
        viz_success = True
        viz_error = None
    except Exception as e:
        fig = None
        viz_success = False
        viz_error = str(e)

    # Create cartoon script
    try:
        cartoon_script = cartoon_gen.generate_cartoon_script(
            query, data, response_context
        )
        cartoon_success = True
        cartoon_error = None
    except Exception as e:
        cartoon_script = None
        cartoon_success = False
        cartoon_error = str(e)

    return {
        "visualization": {
            "figure": fig,
            "success": viz_success,
            "error": viz_error,
            "type": "plotly",
        },
        "cartoon": {
            "script": cartoon_script,
            "success": cartoon_success,
            "error": cartoon_error,
            "type": "dialogue",
        },
        "metadata": {
            "data_rows": len(data) if not data.empty else 0,
            "data_columns": list(data.columns) if not data.empty else [],
            "query_complexity": response_context.get("complexity", "medium"),
        },
    }


def format_cartoon_for_display(cartoon_script: Dict[str, Any]) -> str:
    """
    Format cartoon script for display in your chatbot interface

    Args:
        cartoon_script: Output from EnergyCartoonGenerator

    Returns:
        HTML formatted string for display
    """

    if not cartoon_script or not cartoon_script.get("dialogue"):
        return "<p>No cartoon script available</p>"

    # characters = cartoon_script.get("characters", [])
    dialogue = cartoon_script.get("dialogue", [])
    setting = cartoon_script.get("setting", "Swiss energy discussion")

    # Get character info
    char_info = EnergyCartoonGenerator().characters

    html_parts = [
        "<div class='cartoon-script'>",
        f"<div class='cartoon-setting'><strong>Setting:</strong> {setting}</div>",
        "<div class='cartoon-dialogue'>",
    ]

    for i, exchange in enumerate(dialogue):
        char_key = exchange.get("character", "expert")
        char_data = char_info.get(char_key, {})
        char_name = char_data.get("name", char_key.title())
        char_emoji = char_data.get("emoji", "💭")

        speech_type = exchange.get("type", "speech")
        text = exchange.get("text", "")

        bubble_class = "thought-bubble" if speech_type == "thought" else "speech-bubble"

        html_parts.append(f"""
        <div class='dialogue-exchange'>
            <div class='character-info'>
                <span class='character-emoji'>{char_emoji}</span>
                <span class='character-name'>{char_name}</span>
            </div>
            <div class='{bubble_class}'>
                <p>{text}</p>
            </div>
        </div>
        """)

    html_parts.extend(["</div>", "</div>"])

    return "".join(html_parts)


def get_visualization_config() -> Dict[str, Any]:
    """
    Get configuration for Plotly visualizations

    Returns:
        Configuration dictionary for Plotly figures
    """

    return {
        "toImageButtonOptions": {
            "format": "png",
            "filename": "swiss-energy-chart",
            "height": 600,
            "width": 800,
            "scale": 2,
        },
        "displayModeBar": True,
        "modeBarButtonsToRemove": [
            "pan2d",
            "lasso2d",
            "select2d",
            "autoScale2d",
            "hoverClosestCartesian",
            "hoverCompareCartesian",
        ],
        "displaylogo": False,
        "responsive": True,
    }


# Example usage functions for testing
def test_visualization():
    """Test function to demonstrate visualization capabilities"""

    # Create sample data similar to your extracted CSV structure
    sample_data = pd.DataFrame(
        {
            "scenario": ["ZERO", "WWB", "DIVERGENZ", "ZERO_A", "ZERO_B"],
            "year": [2050] * 5,
            "solar_twh": [45, 25, 35, 50, 40],
            "hydro_twh": [38, 37, 39, 38, 38],
            "emissions_kt": [0, 5000, 2000, 0, 1000],
        }
    )

    # Test different chart types
    visualizer = EnergyVisualizer()

    # This should create a Cleveland plot (>4 categories)
    fig1 = visualizer.create_visualization(
        sample_data, "Compare solar across all scenarios"
    )

    # This should create a bar plot (≤4 categories)
    sample_data_small = sample_data.head(3)
    fig2 = visualizer.create_visualization(sample_data_small, "Compare main scenarios")

    return fig1, fig2


def test_cartoon():
    """Test function to demonstrate cartoon script generation"""

    sample_data = pd.DataFrame(
        {"scenario": ["ZERO", "WWB", "DIVERGENZ"], "solar_twh": [45, 25, 35]}
    )

    cartoon_gen = EnergyCartoonGenerator()

    # Test different script types
    scripts = []
    queries = [
        "Compare solar energy across scenarios",
        "What's the future of Swiss energy?",
        "How much will the energy transition cost?",
        "What are the winter energy challenges?",
    ]

    for query in queries:
        script = cartoon_gen.generate_cartoon_script(
            query, sample_data, {"complexity": "intermediate"}
        )
        scripts.append((query, script))

    return scripts


# CSS styles for cartoon display (add to your chatbot's CSS)
CARTOON_CSS = """
<style>
.cartoon-script {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border: 2px solid #e9ecef;
}

.cartoon-setting {
    background: #f8f9fa;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-style: italic;
    color: #495057;
    border-left: 4px solid #007bff;
}

.dialogue-exchange {
    display: flex;
    margin-bottom: 20px;
    align-items: flex-start;
    gap: 15px;
}

.character-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 80px;
    text-align: center;
}

.character-emoji {
    font-size: 2em;
    margin-bottom: 5px;
}

.character-name {
    font-size: 0.9em;
    font-weight: bold;
    color: #495057;
}

.speech-bubble, .thought-bubble {
    flex: 1;
    background: white;
    padding: 15px 20px;
    border-radius: 20px;
    position: relative;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border: 2px solid #dee2e6;
}

.thought-bubble {
    background: #e3f2fd;
    border: 2px dashed #2196f3;
}

.speech-bubble::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 20px;
    border: 10px solid transparent;
    border-right-color: #dee2e6;
}

.speech-bubble::after {
    content: '';
    position: absolute;
    left: -8px;
    top: 22px;
    border: 8px solid transparent;
    border-right-color: white;
}

.speech-bubble p, .thought-bubble p {
    margin: 0;
    line-height: 1.5;
    color: #495057;
}

@media (max-width: 768px) {
    .dialogue-exchange {
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .speech-bubble::before, .speech-bubble::after {
        display: none;
    }
}
</style>
"""


if __name__ == "__main__":
    # Test the integration
    print("Testing Energy Visualization Integration...")

    # Test visualizations
    fig1, fig2 = test_visualization()
    print(f"Generated visualizations: {type(fig1).__name__}, {type(fig2).__name__}")

    # Test cartoon scripts
    scripts = test_cartoon()
    print(f"Generated {len(scripts)} cartoon scripts")

    for query, script in scripts:
        print(f"\nQuery: {query}")
        print(f"Script type: {script['script_type']}")
        print(f"Characters: {script['characters']}")
        print(f"Dialogue exchanges: {len(script['dialogue'])}")

    print("\nIntegration module ready for chatbot use!")
