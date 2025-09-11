# 🇨🇭 Swiss Energy Scenarios Decipher System - Usage Guide

## ✅ System Status
Your multiagent system is **READY TO USE**! 

✅ **103 data files** processed (74 synthesis + 13 transformation + 16 reports)  
✅ **All 5 AI agents** successfully initialized  
✅ **OpenAI integration** configured and tested  

## 🚀 Quick Start

### 1. **Activate Environment**
```bash
source .venv/bin/activate
```

### 2. **Choose Your Interface**

#### **🖥️ Command Line Interface (Interactive Chat)**
```bash
python main.py
```
- Interactive question/answer format
- User type selection (citizen, journalist, student, policymaker)
- Full conversation history
- Built-in help and examples

#### **🌐 Web Interface (Streamlit)**
```bash
streamlit run streamlit_app.py
```
- Modern web-based interface
- Visual data displays and statistics
- Interactive query suggestions
- Conversation history with expandable details

#### **🔬 Quick Demo**
```bash
python3 run_demo.py
```
- Test the system with a sample query
- Verify all components are working
- See example output format

## 🎯 User Types & Tailored Responses

Select your user type to get responses optimized for your needs:

### 👥 **Citizens**
- Simple, practical explanations
- Focus on everyday impacts
- Clear, jargon-free language
- Local relevance emphasis

### 📰 **Journalists** 
- Facts with supporting context
- Story angles and implications
- Quotable insights and statistics
- Source verification and credibility

### 🎓 **Students**
- Educational explanations of concepts
- Methodology and learning context
- Step-by-step analysis approach
- Additional resources for deeper study

### 🏢 **Policymakers**
- Comprehensive analysis with implications
- Implementation pathways and challenges
- Stakeholder considerations
- Policy recommendations and next steps

## 💡 Example Queries by Category

### 📊 **Data Analysis Questions**
```
"What are Switzerland's CO2 emissions in 2030 under the ZERO scenario?"
"How does electricity consumption change by sector from 2020 to 2050?"
"Compare renewable energy growth between scenarios"
"Show me transport energy consumption trends"
"What is the role of heat pumps in Swiss buildings by 2050?"
```

### 🔮 **Scenario Comparison Questions**
```
"What's the difference between ZERO-Basis and WWB scenarios?"
"How do scenarios differ in nuclear power assumptions?"
"Compare costs between energy transition pathways"
"What are the implications of delayed climate action?"
"Which scenario is more realistic for achieving net-zero by 2050?"
```

### 📄 **Document & Research Questions**
```
"What methodology is used for scenario modeling?"
"Explain the assumptions about biomass availability"
"What do the technical reports say about winter electricity?"
"Find information about carbon capture and storage"
"What are the key uncertainties in the scenarios?"
```

### 🏛️ **Policy & Implementation Questions**
```
"What policies are needed to achieve net-zero by 2050?"
"How does the CO2 Act support the energy transition?"
"What are the implementation challenges for renewable energy?"
"Explain Switzerland's climate commitments"
"What role do cantons play in energy policy?"
```

## 🤖 Available AI Agents

Your system includes 5 specialized agents:

1. **🎯 Orchestrator** - Routes queries and synthesizes responses
2. **📊 Data Interpreter** - Analyzes CSV data and statistics (87 files)  
3. **🔮 Scenario Analyst** - Compares energy transition pathways
4. **📄 Document Intelligence** - Processes PDF reports (16 documents)
5. **🏛️ Policy Context** - Provides Swiss energy policy expertise

## 📈 Data Coverage

### **Energy Data (87 CSV Files)**
- **Demographics & Economics**: Population, GDP, energy prices
- **Emissions**: GHG, CO2, CH4, N2O, F-gases by sector
- **Energy Consumption**: By fuel type, sector, and end use
- **Electricity**: Generation, consumption, capacity, prices
- **Renewables**: Solar, wind, hydro, biomass deployment
- **Sectors**: Transport, buildings, industry, agriculture
- **Technologies**: Heat pumps, power-to-X, district heating
- **Economics**: Costs, investments, price impacts

### **Technical Documents (16 PDF Files)**
- Methodology reports and technical details
- Executive summaries and key findings  
- Specialized studies on specific topics
- Stakeholder consultations and feedback

### **Scenarios Available**
- **ZERO-Basis**: Net-zero emissions by 2050 pathway
- **WWB**: Business-as-usual reference case
- **Variants**: Different technology and policy assumptions

## 🎪 Tips for Better Results

### ✅ **Be Specific**
- Include time periods: "by 2030", "in 2050"
- Mention sectors: "transport", "buildings", "electricity"
- Specify scenarios: "ZERO scenario", "business as usual"

### ✅ **Ask Follow-ups** 
- Use suggested questions provided in responses
- Request scenario comparisons
- Ask for policy implications

### ✅ **Explore Different Angles**
- Try the same question from different user perspectives
- Ask for both technical details and simple explanations
- Request data sources and methodology information

## 🔧 System Commands

### **In CLI Mode:**
- `help` - Show detailed help and examples
- `agents` - List all available AI agents  
- `history` - View conversation history
- `clear` - Clear conversation history
- `user` - Change user type
- `quit` or `exit` - Exit the system

## 🎉 Your System is Ready!

The Swiss Energy Scenarios Decipher System successfully transforms complex energy data into accessible insights. With **103 data files** and **5 specialized AI agents**, you can now:

- ✅ **Analyze** 50+ years of Swiss energy data
- ✅ **Compare** different energy transition scenarios
- ✅ **Understand** technical reports and methodologies  
- ✅ **Explore** policy implications and implementation challenges
- ✅ **Get** answers tailored to your expertise level

**Happy exploring!** 🇨🇭