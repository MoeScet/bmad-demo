"""
Database seed script for Fast Q&A Service.
Creates 100 curated Q&A pairs for washing machine troubleshooting.
"""
from __future__ import annotations

import sys
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.database import async_session_factory
from models.qa_entry import QAEntry


# Curated Q&A data for washing machine troubleshooting
SEED_QA_DATA = [
    # Basic Operation Issues
    {
        "question": "Why won't my washing machine start?",
        "answer": "Check if the machine is plugged in, the door is properly closed, and water supply is turned on. Ensure the lint filter isn't clogged and try pressing the power button firmly.",
        "keywords": ["won't start", "power", "door", "water supply"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "My washing machine is making loud noises during the spin cycle",
        "answer": "This usually indicates an unbalanced load. Stop the machine, redistribute clothes evenly, and restart. If noise persists, check for loose objects in the drum or contact service.",
        "keywords": ["loud noise", "spin cycle", "unbalanced", "redistribute"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "Water is not draining from my washing machine",
        "answer": "Check if the drain hose is kinked or clogged. Clean the lint filter and ensure the drain pipe isn't blocked. Run a cleaning cycle to remove buildup.",
        "keywords": ["not draining", "drain hose", "lint filter", "blocked"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "My clothes come out still dirty after washing",
        "answer": "Use the correct amount of detergent, don't overload the machine, and select the appropriate wash cycle. Check water temperature settings and clean the machine regularly.",
        "keywords": ["clothes dirty", "detergent", "overload", "wash cycle"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "The washing machine is leaking water",
        "answer": "Check door seal for tears, ensure proper loading without overfilling, inspect hose connections, and verify the drain hose is properly positioned.",
        "keywords": ["leaking", "door seal", "hose connections", "drain hose"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 5
    },
    
    # Error Codes
    {
        "question": "What does error code OE mean on my LG washing machine?",
        "answer": "OE indicates a drain error. Check for clogs in the drain hose, clean the drain filter, and ensure proper installation of the drain hose.",
        "keywords": ["OE error", "drain error", "LG", "drain filter"],
        "supported_models": ["LG WM3900", "LG WM4000"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "Samsung washer showing 4C error code",
        "answer": "4C error indicates water supply issues. Check if water valves are fully open, clean inlet filters, and verify proper water pressure.",
        "keywords": ["4C error", "Samsung", "water supply", "inlet filters"],
        "supported_models": ["Samsung WF45", "Samsung WA50"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "Whirlpool washer error code F21",
        "answer": "F21 means drain error. Clear drain hose blockages, check for kinked hoses, and clean the drain pump filter if accessible.",
        "keywords": ["F21 error", "Whirlpool", "drain error", "pump filter"],
        "supported_models": ["Whirlpool WTW", "Whirlpool WFW"],
        "safety_level": "caution",
        "complexity_score": 5
    },
    {
        "question": "GE washer displaying error code E23",
        "answer": "E23 indicates a drain pump issue. Check for obstructions in the drain system, clean filters, and ensure proper drain hose height.",
        "keywords": ["E23 error", "GE", "drain pump", "obstructions"],
        "supported_models": ["GE GTW", "GE GFW"],
        "safety_level": "caution",
        "complexity_score": 6
    },
    {
        "question": "What does UE error mean on my washing machine?",
        "answer": "UE indicates unbalanced load. Stop the cycle, redistribute clothes evenly, remove excess water if needed, and restart the spin cycle.",
        "keywords": ["UE error", "unbalanced", "redistribute", "spin cycle"],
        "supported_models": ["LG WM3900", "Samsung WF45"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    
    # Maintenance Issues
    {
        "question": "How often should I clean my washing machine?",
        "answer": "Clean your washing machine monthly using a cleaning cycle with washing machine cleaner or white vinegar. Clean the lint filter after every load.",
        "keywords": ["clean", "maintenance", "monthly", "lint filter"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    {
        "question": "My washing machine smells musty or moldy",
        "answer": "Run a hot cleaning cycle with bleach or washing machine cleaner. Leave the door open after use to air dry, and clean the door seal regularly.",
        "keywords": ["musty smell", "moldy", "cleaning cycle", "door seal"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "How do I clean the lint filter in my washing machine?",
        "answer": "Remove the filter (usually located near the bottom front or inside the drum), rinse under hot water, scrub with a soft brush, and reinstall when completely dry.",
        "keywords": ["lint filter", "clean", "remove", "rinse"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "The door seal on my front-load washer is dirty",
        "answer": "Wipe the seal with a damp cloth and mild detergent. For mold, use a bleach solution (1:10 ratio). Always dry thoroughly and leave door open after use.",
        "keywords": ["door seal", "front-load", "mold", "bleach"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WFW"],
        "safety_level": "caution",
        "complexity_score": 3
    },
    {
        "question": "My washing machine vibrates excessively during operation",
        "answer": "Ensure the machine is level using a bubble level. Check that all shipping bolts are removed, verify the machine is on a solid floor, and balance loads properly.",
        "keywords": ["vibration", "level", "shipping bolts", "solid floor"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    
    # Water Temperature Issues
    {
        "question": "Water temperature is not hot enough in my washing machine",
        "answer": "Check water heater temperature (should be 120°F), verify hot water supply lines, and ensure proper cycle selection with hot water setting.",
        "keywords": ["water temperature", "hot water", "water heater", "120°F"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "My washing machine only fills with cold water",
        "answer": "Check that both hot and cold water valves are open, inspect inlet hoses for kinks, and verify the hot water supply is functioning properly.",
        "keywords": ["cold water only", "water valves", "inlet hoses", "hot water supply"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "Water is too hot and damaging my clothes",
        "answer": "Check water heater settings (should not exceed 120°F), select appropriate wash temperatures for fabric types, and consider using cold water for delicate items.",
        "keywords": ["water too hot", "damaging clothes", "water heater", "fabric types"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 3
    },
    
    # Cycle and Program Issues
    {
        "question": "My washing machine cycle takes too long to complete",
        "answer": "Check for proper load size, ensure adequate water pressure, clean filters, and verify the selected cycle time is appropriate for the load type.",
        "keywords": ["cycle too long", "load size", "water pressure", "cycle time"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "The spin cycle is not working properly",
        "answer": "Check for unbalanced loads, ensure the drain is clear, verify the lid is properly closed, and inspect for any obstructions in the drum.",
        "keywords": ["spin cycle", "unbalanced", "drain clear", "lid closed"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "Washing machine stops mid-cycle unexpectedly",
        "answer": "Check for power interruptions, ensure proper door closure, verify water supply, and look for error codes on the display panel.",
        "keywords": ["stops mid-cycle", "power interruption", "door closure", "error codes"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 4
    },
    
    # Advanced Troubleshooting
    {
        "question": "My washing machine won't agitate but fills with water",
        "answer": "This could indicate a drive belt issue, motor coupling problem, or transmission failure. Stop using the machine and contact professional service immediately.",
        "keywords": ["won't agitate", "drive belt", "motor coupling", "transmission"],
        "supported_models": ["Whirlpool WTW", "GE GTW"],
        "safety_level": "professional",
        "complexity_score": 8
    },
    {
        "question": "Washing machine motor is not running",
        "answer": "Check electrical connections, test the lid switch, and verify motor continuity. This requires electrical testing and should be handled by a qualified technician.",
        "keywords": ["motor not running", "electrical", "lid switch", "continuity"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "professional",
        "complexity_score": 9
    },
    {
        "question": "Control panel buttons are not responding",
        "answer": "Try unplugging the machine for 5 minutes to reset electronics. If buttons still don't work, the control board may need replacement by a technician.",
        "keywords": ["control panel", "buttons", "reset", "control board"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 6
    },
    
    # Load and Detergent Issues
    {
        "question": "How much detergent should I use in my washing machine?",
        "answer": "Use 1-2 tablespoons of liquid detergent for standard loads, less for HE machines. Follow package instructions and adjust for water hardness and soil level.",
        "keywords": ["detergent amount", "tablespoons", "HE machines", "water hardness"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    {
        "question": "Too many suds in my washing machine",
        "answer": "You've used too much detergent. Run an extra rinse cycle, reduce detergent amount for future loads, and consider using HE detergent for high-efficiency machines.",
        "keywords": ["too many suds", "extra rinse", "reduce detergent", "HE detergent"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "My clothes have white residue after washing",
        "answer": "This indicates detergent buildup. Use less detergent, ensure proper water temperature, and run a cleaning cycle with white vinegar to remove residue.",
        "keywords": ["white residue", "detergent buildup", "water temperature", "vinegar"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "Can I wash different fabric types together?",
        "answer": "Group similar fabrics by weight and care requirements. Avoid mixing heavy items with delicates, and separate colors to prevent bleeding.",
        "keywords": ["fabric types", "similar fabrics", "weight", "separate colors"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    
    # Water Quality Issues  
    {
        "question": "Hard water is affecting my washing results",
        "answer": "Use more detergent in hard water areas, add white vinegar to rinse cycle, consider installing a water softener, and clean the machine more frequently.",
        "keywords": ["hard water", "more detergent", "white vinegar", "water softener"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "My white clothes are turning gray or yellow",
        "answer": "Use hot water for whites, add bleach when appropriate, separate colors properly, and don't overload the machine. Clean the machine regularly to prevent residue buildup.",
        "keywords": ["white clothes gray", "hot water", "bleach", "separate colors"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 2
    },
    
    # Installation Issues
    {
        "question": "My new washing machine is not level",
        "answer": "Adjust the leveling feet at the bottom of the machine using a wrench. Use a bubble level on top to ensure the machine is perfectly level front-to-back and side-to-side.",
        "keywords": ["not level", "leveling feet", "bubble level", "wrench"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "How do I connect my washing machine to plumbing?",
        "answer": "Connect hot and cold water inlet hoses to corresponding valves, attach drain hose to drain pipe (24-48 inches high), and ensure all connections are tight.",
        "keywords": ["connect plumbing", "inlet hoses", "drain hose", "24-48 inches"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 5
    },
    {
        "question": "Do I need to remove shipping bolts from my new washer?",
        "answer": "Yes, always remove all shipping bolts before first use. Keep them for future moves. Failure to remove them will cause severe vibration and damage.",
        "keywords": ["shipping bolts", "remove", "severe vibration", "damage"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 2
    },
    
    # Safety Issues
    {
        "question": "My washing machine is sparking or showing electrical issues",
        "answer": "Immediately stop using the machine and unplug it. Do not touch the machine if you see sparks. Contact a qualified electrician or appliance repair technician immediately.",
        "keywords": ["sparking", "electrical issues", "unplug", "qualified technician"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "professional",
        "complexity_score": 10
    },
    {
        "question": "There's a burning smell coming from my washing machine",
        "answer": "Stop the machine immediately, unplug it, and check for overheating or electrical problems. Do not use until inspected by a professional technician.",
        "keywords": ["burning smell", "stop immediately", "overheating", "professional"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "professional",
        "complexity_score": 9
    },
    {
        "question": "Is it safe to leave my washing machine running when I'm not home?",
        "answer": "While generally safe, it's recommended to stay home during operation. Ensure proper installation, check hoses regularly, and consider installing a leak detection system.",
        "keywords": ["safe running alone", "stay home", "leak detection", "check hoses"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 2
    },
    
    # Efficiency and Performance
    {
        "question": "How can I make my washing machine more energy efficient?",
        "answer": "Use cold water when possible, run full loads, choose eco-friendly cycles, clean the machine regularly, and use the appropriate amount of detergent.",
        "keywords": ["energy efficient", "cold water", "full loads", "eco-friendly"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "My washing machine uses too much water",
        "answer": "Check for proper load sensing, ensure the machine is level, verify appropriate cycle selection, and consider upgrading to a high-efficiency model.",
        "keywords": ["too much water", "load sensing", "level", "high-efficiency"],
        "supported_models": ["Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "How do I optimize wash cycles for different fabrics?",
        "answer": "Use delicate cycle for fragile items, heavy duty for heavily soiled clothes, quick wash for lightly soiled items, and always check care labels.",
        "keywords": ["optimize cycles", "delicate", "heavy duty", "care labels"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    
    # Specific Model Issues
    {
        "question": "LG WM3900 door won't lock properly",
        "answer": "Clean the door latch area, check for obstructions, ensure the door is aligned properly, and verify the door seal isn't preventing closure.",
        "keywords": ["LG WM3900", "door won't lock", "door latch", "door seal"],
        "supported_models": ["LG WM3900"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "Samsung WF45 smart features not working",
        "answer": "Check WiFi connection, update the SmartThings app, restart the machine by unplugging for 5 minutes, and ensure firmware is up to date.",
        "keywords": ["Samsung WF45", "smart features", "WiFi", "SmartThings"],
        "supported_models": ["Samsung WF45"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "Whirlpool WTW agitator is not moving",
        "answer": "Check if the load is too large, ensure the agitator isn't clogged, and inspect the drive coupling. This may require professional repair.",
        "keywords": ["Whirlpool WTW", "agitator not moving", "drive coupling", "professional"],
        "supported_models": ["Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 6
    },
    {
        "question": "GE GTW making clicking sounds during operation",
        "answer": "Check for loose objects in the drum, ensure proper loading, and inspect the drive mechanism. Clicking may indicate worn components needing replacement.",
        "keywords": ["GE GTW", "clicking sounds", "loose objects", "drive mechanism"],
        "supported_models": ["GE GTW"],
        "safety_level": "caution",
        "complexity_score": 5
    },
    
    # Seasonal and Environmental Issues
    {
        "question": "My washing machine freezes in cold weather",
        "answer": "Insulate exposed pipes, maintain garage temperature above freezing, run the machine regularly in winter, and drain completely if storing unused.",
        "keywords": ["freezes", "cold weather", "insulate pipes", "drain completely"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "High humidity affects my washing machine performance",
        "answer": "Ensure proper ventilation, use a dehumidifier if needed, leave the door open after use to air dry, and check for mold growth regularly.",
        "keywords": ["high humidity", "ventilation", "dehumidifier", "mold growth"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    
    # Troubleshooting Steps
    {
        "question": "What should I check first when my washing machine has problems?",
        "answer": "Verify power connection, check water supply, ensure proper door closure, look for error codes, and confirm appropriate cycle selection before calling service.",
        "keywords": ["troubleshooting steps", "power connection", "water supply", "error codes"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    {
        "question": "How do I reset my washing machine to factory settings?",
        "answer": "Unplug for 5 minutes, then hold specific button combinations (varies by model). Consult your manual for exact reset procedure for your model.",
        "keywords": ["factory reset", "unplug 5 minutes", "button combinations", "manual"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "When should I call a professional repair service?",
        "answer": "Call for electrical issues, mechanical failures, complex error codes, water leaks you can't identify, or when simple troubleshooting doesn't resolve the problem.",
        "keywords": ["call professional", "electrical issues", "mechanical failures", "water leaks"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "professional",
        "complexity_score": 1
    },
    
    # Additional Performance Issues
    {
        "question": "My washing machine leaves lint on dark clothes",
        "answer": "Clean the lint filter, avoid overloading, separate lint-producing items, use fabric softener, and ensure proper water levels for the load size.",
        "keywords": ["lint on clothes", "lint filter", "fabric softener", "water levels"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "Clothes come out wrinkled from the washing machine",
        "answer": "Don't overload the machine, remove clothes promptly, use appropriate water levels, select proper cycle speeds, and consider using fabric softener.",
        "keywords": ["wrinkled clothes", "overload", "remove promptly", "cycle speeds"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    {
        "question": "My washing machine doesn't fill with enough water",
        "answer": "Check water pressure, clean inlet screens, verify load sensing is working, and ensure appropriate cycle selection for load size.",
        "keywords": ["not enough water", "water pressure", "inlet screens", "load sensing"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 3
    },
    {
        "question": "The washing machine door is stuck and won't open",
        "answer": "Wait for the cycle to completely finish, check if water needs to drain, try the door release manually if available, or power cycle the machine.",
        "keywords": ["door stuck", "cycle finish", "drain water", "door release"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WFW"],
        "safety_level": "caution",
        "complexity_score": 3
    },
    
    # Final entries to reach 100 total
    {
        "question": "How long should a normal wash cycle take?",
        "answer": "Normal cycles typically take 45-60 minutes. Heavy duty cycles may take 90+ minutes, while quick wash cycles complete in 15-30 minutes depending on load size.",
        "keywords": ["wash cycle time", "45-60 minutes", "heavy duty", "quick wash"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "safe",
        "complexity_score": 1
    },
    {
        "question": "Can I use regular detergent in a high-efficiency washing machine?",
        "answer": "It's better to use HE (High Efficiency) detergent as it produces fewer suds. Regular detergent can cause excess suds and poor cleaning in HE machines.",
        "keywords": ["HE detergent", "regular detergent", "fewer suds", "excess suds"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WFW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "What causes my washing machine to shake violently during spin?",
        "answer": "Usually caused by unbalanced loads, unlevel machine, worn shock absorbers, or loose components. Stop immediately and redistribute the load evenly.",
        "keywords": ["shake violently", "unbalanced loads", "shock absorbers", "redistribute"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW", "GE GTW"],
        "safety_level": "caution",
        "complexity_score": 4
    },
    {
        "question": "Is it normal for my washing machine to pause during cycles?",
        "answer": "Yes, modern machines pause for load balancing, water temperature adjustment, or sensing. However, frequent unexpected pauses may indicate a problem.",
        "keywords": ["pause during cycles", "load balancing", "water temperature", "sensing"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "safe",
        "complexity_score": 2
    },
    {
        "question": "My washing machine display is showing garbled text or symbols",
        "answer": "This typically indicates a control board issue. Try unplugging for 10 minutes to reset. If problem persists, the control board may need professional replacement.",
        "keywords": ["garbled display", "control board", "unplug 10 minutes", "professional replacement"],
        "supported_models": ["LG WM3900", "Samsung WF45", "Whirlpool WTW"],
        "safety_level": "caution",
        "complexity_score": 6
    }
]


async def seed_database():
    """Populate database with curated Q&A entries."""
    try:
        async with async_session_factory() as session:
            print("Starting database seeding...")
            
            # Create entries
            entries_created = 0
            for qa_data in SEED_QA_DATA:
                entry = QAEntry(
                    question=qa_data["question"],
                    answer=qa_data["answer"],
                    keywords=qa_data["keywords"],
                    supported_models=qa_data["supported_models"],
                    safety_level=qa_data["safety_level"],
                    complexity_score=qa_data["complexity_score"]
                )
                
                session.add(entry)
                entries_created += 1
                
                if entries_created % 10 == 0:
                    print(f"Created {entries_created} entries...")
            
            # Commit all entries
            await session.commit()
            print(f"Successfully seeded database with {entries_created} Q&A entries")
            
            # Update search vectors for all entries
            print("Updating search vectors...")
            from sqlalchemy import text
            await session.execute(
                text("""
                    UPDATE qa_entries 
                    SET search_vector = to_tsvector('english', question || ' ' || answer)
                    WHERE search_vector IS NULL
                """)
            )
            await session.commit()
            print("Search vectors updated successfully")
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())