/*
# 1. Create a new React app
npx create-react-app dt-mas-diagrams
cd dt-mas-diagrams

# 2. Install required dependency
npm install lucide-react

# 3. Replace src/App.js with the diagram code

# 4. Start the development server
npm start
*/

import React, { useState } from 'react';
import { ArrowRight, Database, Cpu, Radio, Wifi, MessageSquare } from 'lucide-react';

const SystemDiagrams = () => {
  const [activeTab, setActiveTab] = useState('architecture');

  const ArchitectureDiagram = () => (
    <svg viewBox="0 0 1000 700" className="w-full h-full">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
        </marker>
        <marker id="arrowhead-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#10b981" />
        </marker>
        <marker id="arrowhead-orange" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#f97316" />
        </marker>
        <marker id="arrowhead-reverse" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto">
          <polygon points="10 0, 0 3, 10 6" fill="#3b82f6" />
        </marker>
        <marker id="arrowhead-green-reverse" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto">
          <polygon points="10 0, 0 3, 10 6" fill="#10b981" />
        </marker>
        <marker id="arrowhead-orange-reverse" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto">
          <polygon points="10 0, 0 3, 10 6" fill="#f97316" />
        </marker>
        <marker id="arrowhead-blue-reverse" markerWidth="10" markerHeight="10" refX="1" refY="3" orient="auto">
          <polygon points="10 0, 0 3, 10 6" fill="#3b82f6" />
        </marker>
      </defs>
      
      {/* Title */}
      <text x="370" y="30" textAnchor="middle" className="text-xl font-bold" fill="#1f2937">
        Overall System Architecture
      </text>
      
      {/* BACKGROUND LAYER - Dotted lines to routing system (MOVED HERE - DRAWS FIRST) */}
      <g id="routing-connections" opacity="0.5">
        <line x1="230" y1="250" x2="770" y2="250" stroke="#eab308" strokeWidth="1.5" strokeDasharray="5,5"/>
        <line x1="460" y1="270" x2="770" y2="270" stroke="#eab308" strokeWidth="1.5" strokeDasharray="5,5"/>
        <line x1="690" y1="290" x2="770" y2="290" stroke="#eab308" strokeWidth="1.5" strokeDasharray="5,5"/>
      </g>
      
      {/* Manager Agent */}
      <rect x="270" y="60" width="200" height="100" rx="8" fill="#dbeafe" stroke="#3b82f6" strokeWidth="2"/>
      <text x="370" y="90" textAnchor="middle" className="font-semibold" fill="#1e40af">Manager Agent</text>
      <text x="370" y="110" textAnchor="middle" className="text-sm" fill="#1e40af">Port: 8000</text>
      <text x="370" y="125" textAnchor="middle" className="text-xs" fill="#64748b">Task Generation</text>
      <text x="370" y="140" textAnchor="middle" className="text-xs" fill="#64748b">Task Allocation</text>
      
      {/* Vehicle Agents */}
      <g id="vehicle-agents">
        <rect x="50" y="220" width="180" height="100" rx="8" fill="#dcfce7" stroke="#10b981" strokeWidth="2"/>
        <text x="140" y="245" textAnchor="middle" className="font-semibold" fill="#065f46">Vehicle Agent 1</text>
        <text x="140" y="265" textAnchor="middle" className="text-xs" fill="#065f46">Port: 8001</text>
        <text x="140" y="285" textAnchor="middle" className="text-xs" fill="#065f46">Priority: Distance</text>
        <text x="140" y="305" textAnchor="middle" className="text-xs" fill="#64748b">Route Planning</text>
        
        <rect x="280" y="220" width="180" height="100" rx="8" fill="#dcfce7" stroke="#10b981" strokeWidth="2"/>
        <text x="370" y="245" textAnchor="middle" className="font-semibold" fill="#065f46">Vehicle Agent 2</text>
        <text x="370" y="265" textAnchor="middle" className="text-xs" fill="#065f46">Port: 8002</text>
        <text x="370" y="285" textAnchor="middle" className="text-xs" fill="#065f46">Priority: Carbon</text>
        <text x="370" y="305" textAnchor="middle" className="text-xs" fill="#64748b">Route Planning</text>
        
        <rect x="510" y="220" width="180" height="100" rx="8" fill="#dcfce7" stroke="#10b981" strokeWidth="2"/>
        <text x="600" y="245" textAnchor="middle" className="font-semibold" fill="#065f46">Vehicle Agent 3</text>
        <text x="600" y="265" textAnchor="middle" className="text-xs" fill="#065f46">Port: 8003</text>
        <text x="600" y="285" textAnchor="middle" className="text-xs" fill="#065f46">Priority: Cost</text>
        <text x="600" y="305" textAnchor="middle" className="text-xs" fill="#64748b">Route Planning</text>
      </g>
      
      {/* Digital Twins */}
      <g id="digital-twins">
        <rect x="50" y="400" width="180" height="100" rx="8" fill="#fed7aa" stroke="#f97316" strokeWidth="2"/>
        <text x="140" y="425" textAnchor="middle" className="font-semibold" fill="#9a3412">Digital Twin 1</text>
        <text x="140" y="445" textAnchor="middle" className="text-xs" fill="#9a3412">TCP Port: 5000</text>
        <text x="140" y="460" textAnchor="middle" className="text-xs" fill="#9a3412">MQTT: vehicle1</text>
        <text x="140" y="475" textAnchor="middle" className="text-xs" fill="#64748b">Data Translation</text>
        <text x="140" y="490" textAnchor="middle" className="text-xs" fill="#64748b">State Tracking</text>
        
        <rect x="280" y="400" width="180" height="100" rx="8" fill="#fed7aa" stroke="#f97316" strokeWidth="2"/>
        <text x="370" y="425" textAnchor="middle" className="font-semibold" fill="#9a3412">Digital Twin 2</text>
        <text x="370" y="445" textAnchor="middle" className="text-xs" fill="#9a3412">TCP Port: 5001</text>
        <text x="370" y="460" textAnchor="middle" className="text-xs" fill="#9a3412">MQTT: vehicle2</text>
        <text x="370" y="475" textAnchor="middle" className="text-xs" fill="#64748b">Data Translation</text>
        <text x="370" y="490" textAnchor="middle" className="text-xs" fill="#64748b">State Tracking</text>
        
        <rect x="510" y="400" width="180" height="100" rx="8" fill="#fed7aa" stroke="#f97316" strokeWidth="2"/>
        <text x="600" y="425" textAnchor="middle" className="font-semibold" fill="#9a3412">Digital Twin 3</text>
        <text x="600" y="445" textAnchor="middle" className="text-xs" fill="#9a3412">TCP Port: 5002</text>
        <text x="600" y="460" textAnchor="middle" className="text-xs" fill="#9a3412">MQTT: vehicle3</text>
        <text x="600" y="475" textAnchor="middle" className="text-xs" fill="#64748b">Data Translation</text>
        <text x="600" y="490" textAnchor="middle" className="text-xs" fill="#64748b">State Tracking</text>
      </g>
      
      {/* Vehicle Simulator */}
      <rect x="50" y="580" width="640" height="80" rx="8" fill="#e0e7ff" stroke="#6366f1" strokeWidth="2"/>
      <text x="370" y="610" textAnchor="middle" className="font-semibold" fill="#3730a3">Vehicle Simulator</text>
      <text x="370" y="630" textAnchor="middle" className="text-xs" fill="#3730a3">MQTT Broker: localhost:4001</text>
      <text x="370" y="645" textAnchor="middle" className="text-xs" fill="#64748b">Physical Vehicle Simulation</text>
      
      {/* Routing System (side component) */}
      <rect x="770" y="220" width="200" height="280" rx="8" fill="#fef3c7" stroke="#eab308" strokeWidth="2"/>
      <text x="870" y="245" textAnchor="middle" className="font-semibold" fill="#713f12">Routing System</text>
      <text x="870" y="265" textAnchor="middle" className="text-xs" fill="#713f12">(route.py)</text>
      <text x="870" y="290" textAnchor="middle" className="text-xs" fill="#64748b">1) Network Topology</text>
      <text x="870" y="310" textAnchor="middle" className="text-xs" fill="#64748b">2) Dijkstra Algorithm</text>
      <text x="870" y="330" textAnchor="middle" className="text-xs" fill="#64748b">3) Edge Weights:</text>
      <text x="870" y="350" textAnchor="middle" className="text-xs" fill="#64748b">  - Distance</text>
      <text x="870" y="370" textAnchor="middle" className="text-xs" fill="#64748b">  - Carbon</text>
      <text x="870" y="390" textAnchor="middle" className="text-xs" fill="#64748b">  - Cost</text>
      <text x="870" y="415" textAnchor="middle" className="text-xs" fill="#64748b">4) Location Tracking</text>
      <text x="870" y="435" textAnchor="middle" className="text-xs" fill="#64748b">5) Travel Time</text>
      <text x="870" y="460" textAnchor="middle" className="text-xs font-semibold" fill="#713f12">Files:</text>
      <text x="870" y="478" textAnchor="middle" className="text-xs" fill="#64748b">map.txt</text>
      <text x="870" y="493" textAnchor="middle" className="text-xs" fill="#64748b">vehicles.txt</text>
      
      {/* Connections - Manager to Vehicles */}
      <line x1="330" y1="160" x2="140" y2="220" stroke="#3b82f6" strokeWidth="2"  markerStart="url(#arrowhead-blue-reverse)" markerEnd="url(#arrowhead)"/>
      <line x1="370" y1="160" x2="370" y2="220" stroke="#3b82f6" strokeWidth="2"  markerStart="url(#arrowhead-blue-reverse)" markerEnd="url(#arrowhead)"/>
      <line x1="410" y1="160" x2="600" y2="220" stroke="#3b82f6" strokeWidth="2"  markerStart="url(#arrowhead-blue-reverse)" markerEnd="url(#arrowhead)"/>
      <text x="10" y="180" className="text-xs" fill="#3b82f6">uAgents Protocol</text>
      
      {/* Connections - Vehicles to Digital Twins */}
      <line x1="140" y1="320" x2="140" y2="400" stroke="#10b981" strokeWidth="2"  markerStart="url(#arrowhead-green-reverse)" markerEnd="url(#arrowhead-green)"/>
      <line x1="370" y1="320" x2="370" y2="400" stroke="#10b981" strokeWidth="2"  markerStart="url(#arrowhead-green-reverse)" markerEnd="url(#arrowhead-green)"/>
      <line x1="600" y1="320" x2="600" y2="400" stroke="#10b981" strokeWidth="2"  markerStart="url(#arrowhead-green-reverse)" markerEnd="url(#arrowhead-green)"/>
      <text x="10" y="360" className="text-xs" fill="#10b981">TCP</text>
      
      {/* Connections - Digital Twins to Simulator */}
      <line x1="140" y1="500" x2="140" y2="580" stroke="#f97316" strokeWidth="2"  markerStart="url(#arrowhead-orange-reverse)" markerEnd="url(#arrowhead-orange)"/>
      <line x1="370" y1="500" x2="370" y2="580" stroke="#f97316" strokeWidth="2"  markerStart="url(#arrowhead-orange-reverse)" markerEnd="url(#arrowhead-orange)"/>
      <line x1="600" y1="500" x2="600" y2="580" stroke="#f97316" strokeWidth="2"  markerStart="url(#arrowhead-orange-reverse)" markerEnd="url(#arrowhead-orange)"/>
      <text x="10" y="545" className="text-xs" fill="#f97316">MQTT Pub/Sub</text>
      
      {/* TEXT LAYER - "Uses" label (drawn last so it appears on top) */}
      <text x="710" y="240" className="text-xs" fill="#eab308">Uses</text>
    </svg>
  );

  const ProtocolDiagramPhase1 = () => (
        <svg viewBox="0 0 1200 1100" className="w-full h-full">
          <defs>
            <marker id="arrow-black" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#1f2937" />
            </marker>
          </defs>
          
          <rect x="100" y="60" width="1000" height="980" fill="white" stroke="#1f2937" strokeWidth="2.5"/>
          
          {/* This group is now shifted by 150px (100 + 50) */}
          <g transform="translate(150, 0)">
          
            <text x="600" y="30" textAnchor="middle" className="text-xl font-bold" fill="#1f2937">
              FIPA Contract Net Protocol - Proposal & Assignment Phase
            </text>
            
            <g id="participants">
              <rect x="80" y="80" width="160" height="60" rx="5" fill="#dbeafe" stroke="#3b82f6" strokeWidth="2"/>
              <text x="160" y="105" textAnchor="middle" className="font-semibold" fill="#1e40af">Manager</text>
              <text x="160" y="125" textAnchor="middle" className="text-xs" fill="#64748b">(Initiator)</text>
              
              <rect x="280" y="80" width="160" height="60" rx="5" fill="#dcfce7" stroke="#10b981" strokeWidth="2"/>
              <text x="360" y="105" textAnchor="middle" className="font-semibold" fill="#065f46">Vehicle Agent</text>
              <text x="360" y="125" textAnchor="middle" className="text-xs" fill="#64748b">(Participant)</text>
              
              <rect x="480" y="80" width="160" height="60" rx="5" fill="#fed7aa" stroke="#f97316" strokeWidth="2"/>
              <text x="560" y="105" textAnchor="middle" className="font-semibold" fill="#9a3412">Digital Twin</text>
              <text x="560" y="125" textAnchor="middle" className="text-xs" fill="#64748b">(Mediator)</text>
              
              <rect x="680" y="80" width="160" height="60" rx="5" fill="#e0e7ff" stroke="#6366f1" strokeWidth="2"/>
    s         <text x="760" y="105" textAnchor="middle" className="font-semibold" fill="#3730a3">Simulator</text>
              <text x="760" y="125" textAnchor="middle" className="text-xs" fill="#64748b">(Environment)</text>
            </g>
            
            <line x1="160" y1="140" x2="160" y2="1000" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
            <line x1="360" y1="140" x2="360" y2="1000" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
            <line x1="560" y1="140" x2="560" y2="1000" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
            <line x1="760" y1="140" x2="760" y2="1000" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
            
            <text x="70" y="180" className="text-sm font-bold" fill="#1f2937">Phase 1:</text>
            <text x="70" y="195" className="text-sm font-bold" fill="#1f2937">Call for</text>
            <text x="70" y="210" className="text-sm font-bold" fill="#1f2937">Proposal</text>
      
            <g id="msg1">
              <line x1="160" y1="190" x2="360" y2="190" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="260" y="180" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">1. cfp</text>
              <text x="260" y="210" textAnchor="middle" className="text-xs italic" fill="#64748b">(destination_node, task_id)</text>
            </g>
            
            <g id="msg2a-refuse">
              <line x1="360" y1="280" x2="160" y2="280" stroke="#10b981" strokeWidth="2" strokeDasharray="4,4" markerEnd="url(#arrow-black)"/>
              <text x="260" y="270" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">2a. refuse</text>
              <text x="260" y="300" textAnchor="middle" className="text-xs italic" fill="#64748b">(is_busy=true)</text>
            </g>
    
            <g id="msg2b">
              {/* Changed strokeWidth to 2.5 */}
              <line x1="360" y1="280" x2="560" y2="280" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="460" y="270" textAnchor="middle" className="text-xs font-semibold" fill="#a855f7">2b. get_status</text>
              <text x="460" y="300" textAnchor="middle" className="text-xs italic" fill="#64748b">(vehicle_id)</text>
            </g>
    
            <g id="decision1">
              <polygon points="360,265 380,280 360,295 340,280" fill="white" stroke="#10b981" strokeWidth="2"/>
              <text x="360" y="285" textAnchor="middle" className="text-xs font-bold" fill="#065f46">?</text>
              <text x="370" y="245" textAnchor="start" className="text-xs" fill="#64748b">is_busy?</text>
              <text x="370" y="310" textAnchor="start" className="text-xs" fill="#64748b">no</text>
              <text x="320" y="310" textAnchor="start" className="text-xs" fill="#64748b">yes</text>
            </g>      
            
            <g id="msg3">
              {/* Changed strokeWidth to 2.5 */}
              <line x1="560" y1="350" x2="760" y2="350" stroke="#f97316" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="660" y="340" textAnchor="middle" className="text-xs font-semibold" fill="#f97316">3. query_location</text>
              <text x="660" y="367" textAnchor="middle" className="text-xs italic" fill="#64748b">(vehicle_id)</text>
            </g>
            
            <g id="msg4">
              {/* Changed strokeWidth to 2.5 */}
              <line x1="760" y1="390" x2="560" y2="390" stroke="#f97316" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="660" y="383" textAnchor="middle" className="text-xs font-semibold" fill="#f97316">4. location_data</text>
              <text x="660" y="407" textAnchor="middle" className="text-xs italic" fill="#64748b">(current_node, speed)</text>
            </g>
            
            <g id="msg5">
              {/* Changed strokeWidth to 2.5 */}
              <line x1="560" y1="430" x2="360" y2="430" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="460" y="420" textAnchor="middle" className="text-xs font-semibold" fill="#a855f7">5. status_response</text>
              <text x="460" y="447" textAnchor="middle" className="text-xs italic" fill="#64748b">(current_location, speed)</text>
    D       </g>
            
            
            <rect x="310" y="490" width="100" height="60" fill="#fef3c7" stroke="#eab308" strokeWidth="1.5"/>
            <text x="360" y="517" textAnchor="middle" className="text-xs" fill="#713f12">Dijkstra's</text>
            <text x="360" y="532" textAnchor="middle" className="text-xs" fill="#713f12">Algorithm</text>
            
            
            <rect x="310" y="570" width="100" height="45" fill="#dcfce7" stroke="#10b981" strokeWidth="1.5"/>
            <text x="360" y="590" textAnchor="middle" className="text-xs" fill="#065f46">Select</text>
            <text x="360" y="605" textAnchor="middle" className="text-xs" fill="#065f46">Time</text>
    A       
            <g id="msg6">
              <line x1="360" y1="640" x2="160" y2="640" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="260" y="630" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">6. propose</text>
              <text x="260" y="657" textAnchor="middle" className="text-xs italic" fill="#64748b">(travel_time)</text>
            </g>
            
            <text x="70" y="655" className="text-sm font-bold" fill="#1f2937">Phase 2:</text>
            <text x="70" y="670" className="text-sm font-bold" fill="#1f2937">Evaluation</text>
            
            <rect x="110" y="680" width="100" height="60" fill="#dbeafe" stroke="#3b82f6" strokeWidth="1.5"/>
            <text x="160" y="700" textAnchor="middle" className="text-xs" fill="#1e40af">Wait for All</text>
            <text x="160" y="715" textAnchor="middle" className="text-xs" fill="#1e40af">Proposals</text>
            <text x="160" y="730" textAnchor="middle" className="text-xs" fill="#1e40af">(or timeout)</text>
            
            <rect x="100" y="760" width="120" height="40" fill="#dbeafe" stroke="#3b82f6" strokeWidth="1.5"/>
            <text x="160" y="777" textAnchor="middle" className="text-xs" fill="#1e40af">Select Min</text>
            <text x="160" y="792" textAnchor="middle" className="text-xs" fill="#1e40af">Estimated Time</text>
          
    
          
            <g id="msg7">
              {/* Changed strokeWidth to 2.5 (from 3) */}
              <line x1="160" y1="850" x2="360" y2="850" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="260" y="840" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">7. accept-proposal</text>
              <text x="260" y="872" textAnchor="middle" className="text-xs italic" fill="#64748b">(task_id, destination_node)</text>
    ci       </g>
            
            <rect x="310" y="885" width="100" height="45" fill="#dcfce7" stroke="#10b981" strokeWidth="1.5"/>
            <text x="360" y="903" textAnchor="middle" className="text-xs font-bold" fill="#065f46">Set is_busy</text>
            <text x="360" y="920" textAnchor="middle" className="text-xs font-bold" fill="#065f46">= TRUE</text>
    s       
            <g id="msg8">
              {/* Changed strokeWidth to 2.5 */}
              <line x1="360" y1="955" x2="160" y2="955" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
              <text x="260" y="940" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">8. accept</text>
              <text x="260" y="970" textAnchor="middle" className="text-xs italic" fill="#64748b">(accepted=true,</text>
    tr         <text x="260" y="985" textAnchor="middle" className="text-xs italic" fill="#64748b">planned_path)</text>
            </g>
            
            <text x="450" y="1020" textAnchor="middle" className="text-xs italic" fill="#64748b">
              [Continue to Phase 3: Execution Loop]
            </text>
          
          </g> {/* End of the transformed group */}
          
          
          <g id="legend">
            <rect x="60" y="1045" width="1080" height="35" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1" rx="4"/>
    source       
            <line x1="120" y1="1062" x2="160" y2="1062" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
            <text x="170" y="1067" className="text-xs" fill="#64748b">uAgents Protocol</text>
            
            <line x1="310" y1="1062" x2="350" y2="1062" stroke="#f97316" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
            <text x="360" y="1067" className="text-xs" fill="#64748b">MQTT</text>
            
            <line x1="430" y1="1062" x2="470" y2="1062" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
            <text x="480" y="1067" className="text-xs" fill="#64748b">TCP</text>
            
        S   <line x1="540" y1="1062" x2="580" y2="1062" stroke="#eab308" strokeWidth="2.5" markerEnd="url(#arrow-black)"/>
    Services   <text x="590" y="1067" className="text-xs" fill="#64748b">Python Function Call</text>
            
            <line x1="760" y1="1062" x2="800" y2="1062" stroke="#10b981" strokeWidth="2.5" strokeDasharray="4,4" markerEnd="url(#arrow-black)"/>
            <text x="810" y="1067" className="text-xs" fill="#64748b">Refuse/Reject</text>
    s       
            <polygon points="940,1057 950,1062 940,1067 930,1062" fill="white" stroke="#1f2937" strokeWidth="1.5"/>
            <text x="960" y="1067" className="text-xs" fill="#64748b">Decision Point</text>
          </g>
        </svg>
      );

    const ProtocolDiagramPhase2 = () => (
            <svg viewBox="0 0 1000 900" className="w-full h-full">
              <defs>
                <marker id="arrow-black-p2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill="#1f2937" />
                </marker>
              </defs>
              
              <rect x="40" y="60" width="920" height="800" fill="white" stroke="#1f2937" strokeWidth="2.5"/>
              
              {/* Shifted horizontally by 90px */}
              <g transform="translate(90, 0)">
              
                <text x="500" y="30" textAnchor="middle" className="text-xl font-bold" fill="#1f2937">
                  Execution Loop & Completion Phase
                </text>
                
                <g id="participants">
                  <rect x="80" y="80" width="140" height="40" rx="5" fill="#dbeafe" stroke="#3b82f6" strokeWidth="2"/>
                  <text x="150" y="105" textAnchor="middle" className="font-semibold text-sm" fill="#1e40af">Manager</text>
                  
                  <rect x="260" y="80" width="140" height="40" rx="5" fill="#dcfce7" stroke="#10b981" strokeWidth="2"/>
                  <text x="330" y="105" textAnchor="middle" className="font-semibold text-sm" fill="#065f46">Vehicle Agent</text>
                  
                  <rect x="440" y="80" width="140" height="40" rx="5" fill="#fed7aa" stroke="#f97316" strokeWidth="2"/>
      s           <text x="510" y="105" textAnchor="middle" className="font-semibold text-sm" fill="#9a3412">Digital Twin</text>
                  
                  <rect x="620" y="80" width="140" height="40" rx="5" fill="#e0e7ff" stroke="#6366f1" strokeWidth="2"/>
                  <text x="690" y="105" textAnchor="middle" className="font-semibold text-sm" fill="#3730a3">Simulator</text>
                </g>
                
                <line x1="150" y1="120" x2="150" y2="820" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
                <line x1="330" y1="120" x2="330" y2="820" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
                <line x1="510" y1="120" x2="510" y2="820" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
                <line x1="690" y1="120" x2="690" y2="820" stroke="#1f2937" strokeWidth="2" strokeDasharray="8,4"/>
                
                <rect x="300" y="150" width="450" height="460" fill="#fef9e7" fillOpacity="0.3" stroke="#eab308" strokeWidth="2.5" strokeDasharray="5,5" rx="4"/>
      
                <g id="Phase3">
                <text x="60" y="200" className="text-sm font-bold" fill="#1f2937">Phase 3:</text>
                <text x="60" y="215" className="text-sm font-bold" fill="#1f2937">Path </text>
                <text x="60" y="230" className="text-sm font-bold" fill="#1f2937">Execution</text>
                </g>
      
                <g id="msg9">
                  <line x1="330" y1="200" x2="510" y2="200" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
                  <text x="420" y="190" textAnchor="middle" className="text-xs font-semibold" fill="#a855f7">9. assign_mission</text>
                  <text x="420" y="217" textAnchor="middle" className="text-xs italic" fill="#64748b">(destination:</text>
                  <text x="420" y="232" textAnchor="middle" className="text-xs italic" fill="#64748b">next_waypoint)</text>
                </g>
                
                <g id="msg10">
                  <line x1="510" y1="240" x2="690" y2="240" stroke="#f97316" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
                	<text x="600" y="230" textAnchor="middle" className="text-xs font-semibold" fill="#f97316">10. MQTT publish</text>
                	<text x="600" y="257" textAnchor="middle" className="text-xs italic" fill="#64748b">(next_destination)</text>
            	</g>
              
            	<g id="msg11">
              	<line x1="510" y1="280" x2="330" y2="280" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
              	<text x="420" y="270" textAnchor="middle" className="text-xs font-semibold" fill="#a855f7">11. task_ack</text>
            	</g>
              
            	<rect x="640" y="280" width="100" height="40" fill="#e0e7ff" stroke="#6366f1" strokeWidth="1.5"/>
            	<text x="690" y="300" textAnchor="middle" className="text-xs" fill="#3730a3">Move Vehicle</text>
            	<text x="690" y="315" textAnchor="middle" className="text-xs" fill="#3730a3">to Waypoint</text>
            	
      
            
            	<g id="msg12">
              	<line x1="690" y1="400" x2="510" y2="400" stroke="#f97316" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow-black-p2)"/>
              	<text x="600" y="392" textAnchor="middle" className="text-xs font-semibold" fill="#f97316">12. MQTT update</text>
              	<text x="600" y="415" textAnchor="middle" className="text-xs italic" fill="#64748b">(progress,</text>
              	<text x="600" y="430" textAnchor="middle" className="text-xs italic" fill="#64748b">current_node, x, y)</text>
      
            	</g>
            	
            	<g id="msg13">
              	<line x1="510" y1="445" x2="330" y2="445" stroke="#a855f7" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow-black-p2)"/>
              	<text x="420" y="437" textAnchor="middle" className="text-xs font-semibold" fill="#a855f7">13. vehicle_data</text>
              	<text x="420" y="460" textAnchor="middle" className="text-xs italic" fill="#64748b">(mission_progress, </text>
              	<text x="420" y="475" textAnchor="middle" className="text-xs italic" fill="#64748b">current_location)</text>
            	</g>
            	
      
            
            	<g id="decision-waypoint">
              	<polygon points="330,530 350,545 330,560 310,545" fill="white" stroke="#10b981" strokeWidth="2"/>
              	<text x="330" y="549" textAnchor="middle" className="text-xs font-bold" fill="#065f46">?</text>
              	<text x="355" y="550" textAnchor="start" className="text-xs" fill="#64748b">Destination reached?</text>
              	<text x="250" y="550" textAnchor="start" className="text-xs" fill="#64748b">No</text>
              	<text x="335" y="580" textAnchor="start" className="text-xs" fill="#64748b">Yes</text>
      Â     	</g>
            	
            	<line x1="310" y1="545" x2="280" y2="545" stroke="#eab308" strokeWidth="2.5" strokeDasharray="4,4"/>
            	<line x1="280" y1="545" x2="280" y2="200" stroke="#eab308" strokeWidth="2.5" strokeDasharray="4,4"/>
            	<line x1="280" y1="200" x2="300" y2="200" stroke="#eab308" strokeWidth="2.5" strokeDasharray="4,4" markerEnd="url(#arrow-black-p2)"/>
      section   	<text x="210" y="390" className="text-xs font-bold" fill="#eab308" transform="rotate(-90 255 370)">
              	[Next Waypoint]
            	</text>
            	
            	<text x="60" y="630" className="text-sm font-bold" fill="#1f2937">Phase 4:</text>
      Examples   	<text x="60" y="645" className="text-sm font-bold" fill="#1f2937">Completion</text>
            	
            	<rect x="280" y="635" width="100" height="40" fill="#dcfce7" stroke="#10b981" strokeWidth="1.5"/>
            	<text x="330" y="650" textAnchor="middle" className="text-xs font-bold" fill="#065f46">Set is_busy</text>
            	<text x="330" y="667" textAnchor="middle" className="text-xs font-bold" fill="#065f46">= FALSE</text>
            	
            	
            	<g id="msg14">
              	<line x1="330" y1="720" x2="150" y2="720" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
              	<text x="240" y="710" textAnchor="middle" className="text-xs font-semibold" fill="#10b981">14. TaskCompletion</text>
              	<text x="240" y="745" textAnchor="middle" className="text-xs italic" fill="#64748b">(task_id, success=true</text>
      E       	<text x="240" y="765" textAnchor="middle" className="text-xs italic" fill="#64748b">final_node)</text>
      A     	</g>
          
          	</g> {/* End of the transformed group */}
          	
          	
          	<g id="legend">
            	<rect x="60" y="870" width="880" height="30" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1" rx="4"/>
            	
            	<rect x="80" y="877" width="80" height="16" fill="#fef9e7" stroke="#eab308" strokeWidth="1.5" strokeDasharray="5,5" rx="2"/>
            	<text x="170" y="890" className="text-xs" fill="#64748b">Main Loop</text>
          	
            	<line x1="260" y1="885" x2="300" y2="885" stroke="#10b981" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
      Donec   	<text x="320" y="890" className="text-xs" fill="#64748b">uAgents</text>
            	
            	<line x1="390" y1="885" x2="440" y2="885" stroke="#f97316" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
            	<text x="450" y="890" className="text-xs" fill="#64748b">MQTT</text>
            	
            	<line x1="510" y1="885" x2="550" y2="885" stroke="#a855f7" strokeWidth="2.5" markerEnd="url(#arrow-black-p2)"/>
            	<text x="565" y="890" className="text-xs" fill="#64748b">TCP</text>
            	
            	<line x1="620" y1="885" x2="660" y2="885" stroke="#1f2937" strokeWidth="1.5" strokeDasharray="3,3" markerEnd="url(#arrow-black-p2)"/>
            	<text x="670" y="890" className="text-xs" fill="#64748b">Periodic/Async</text>
          
          	<polygon points="810,880 820,885 810,890 800,885" fill="white" stroke="#1f2937" strokeWidth="1.5"/>
          	<text x="830" y="890" className="text-xs" fill="#64748b">Decision Point</text>
          	</g>
         </svg>
        );
  
      const DataFlowDiagram = () => (
        <svg viewBox="0 0 550 580" className="w-full h-full">
          <defs>
            <marker id="arrow-right" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <polygon points="0 0, 8 4, 0 8" fill="#ca8a04" />
            </marker>
            <marker id="arrow-left" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <polygon points="0 0, 8 4, 0 8" fill="#ca8a04" />
            </marker>
          </defs>
          
          {/* Main Container */}
          <rect x="10" y="10" width="530" height="560" rx="12" fill="#fffbeb" stroke="#eab308" strokeWidth="4"/>
          
          {/* Header */}
          <text x="275" y="40" textAnchor="middle" className="text-lg font-bold" fill="#713f12">
            Digital Twin
          </text>
          <text x="275" y="60" textAnchor="middle" className="text-sm italic" fill="#92400e">
            Agent - Simulator Interface
          </text>
          <line x1="30" y1="70" x2="520" y2="70" stroke="#eab308" strokeWidth="2"/>
          
          {/* ===== COMMAND PROCESSING ===== */}
          <g id="command-section">
            <rect x="30" y="85" width="490" height="165" rx="8" fill="#fef3c7" stroke="#ca8a04" strokeWidth="2"/>
            <text x="275" y="108" textAnchor="middle" className="text-sm font-bold" fill="#713f12">
                Command Processing (Agent → Simulator)
            </text>
            
            {/* Receives Box */}
            <rect x="45" y="120" width="200" height="120" rx="6" fill="#ffffff" stroke="#ca8a04" strokeWidth="1.5"/>
            <text x="145" y="138" textAnchor="middle" className="text-xs font-bold" fill="#713f12">
              Receives (TCP):
            </text>
            <text x="55" y="160" className="text-xs" fill="#1e293b">type: "assign_mission"</text>
            <text x="55" y="180" className="text-xs" fill="#1e293b">destination: "Node5"</text>
            <line x1="55" y1="205" x2="235" y2="205" stroke="#d97706" strokeWidth="1" strokeDasharray="3,2"/>
            <text x="55" y="227" className="text-xs font-mono" fill="#64748b">High-level Instructions</text>
            
            {/* Arrow */}
            <line x1="245" y1="180" x2="300" y2="180" stroke="#ca8a04" strokeWidth="2" markerEnd="url(#arrow-right)"/>
            
            {/* Publishes Box */}
            <rect x="305" y="120" width="200" height="120" rx="6" fill="#ffffff" stroke="#ca8a04" strokeWidth="1.5"/>
            <text x="405" y="138" textAnchor="middle" className="text-xs font-bold" fill="#713f12">
              Publishes (MQTT):
            </text>
            <text x="315" y="160" className="text-xs" fill="#1e293b">topic: vehicle1_next_dest</text>
            <text x="315" y="180" className="text-xs" fill="#1e293b">payload: "Node5"</text>
            <line x1="315" y1="205" x2="495" y2="205" stroke="#d97706" strokeWidth="1" strokeDasharray="3,2"/>
            <text x="315" y="225" className="text-xs italic" fill="#16a34a">✓ Logs command</text>
          </g>
          
          {/* ===== STATE HISTORY ===== */}
          <g id="state-section">
            <rect x="30" y="270" width="490" height="70" rx="8" fill="#fde68a" stroke="#d97706" strokeWidth="2"/>
            <text x="275" y="295" textAnchor="middle" className="text-sm font-bold" fill="#713f12">
              📊 State History & Data Model
            </text>
            <text x="45" y="315" className="text-xs" fill="#1e293b">
              • Logs all messages with timestamps
            </text>
            <text x="45" y="332" className="text-xs" fill="#1e293b">
              • Stores both command and telemetry metadata for verification
            </text>
          </g>
          
          {/* ===== TELEMETRY PROCESSING ===== */}
          <g id="telemetry-section">
            <rect x="30" y="360" width="490" height="165" rx="8" fill="#fef3c7" stroke="#ca8a04" strokeWidth="2"/>
            <text x="275" y="383" textAnchor="middle" className="text-sm font-bold" fill="#713f12">
                Telemetry Processing (Simulator → Agent)
            </text>
            
            {/* Receives Box */}
            <rect x="305" y="395" width="200" height="120" rx="6" fill="#ffffff" stroke="#ca8a04" strokeWidth="1.5"/>
            <text x="405" y="413" textAnchor="middle" className="text-xs font-bold" fill="#713f12">
              Receives (MQTT):
            </text>
            <text x="312" y="435" className="text-xs" fill="#1e293b">progress: 75</text>
            <text x="312" y="455" className="text-xs" fill="#1e293b">next_location: "Node5"</text>
            <text x="312" y="475" className="text-xs" fill="#1e293b">previous_location: "Node3"</text>
            <line x1="312" y1="490" x2="495" y2="490" stroke="#d97706" strokeWidth="1" strokeDasharray="3,2"/>
            <text x="385" y="507" textAnchor="middle" className="text-xs italic" fill="#64748b">
              Low-level telemetry
            </text>
            
            {/* Arrow */}
            <line x1="305" y1="455" x2="250" y2="455" stroke="#ca8a04" strokeWidth="2" markerEnd="url(#arrow-left)"/>
            
            {/* Forwards Box */}
            <rect x="45" y="395" width="200" height="120" rx="6" fill="#ffffff" stroke="#ca8a04" strokeWidth="1.5"/>
            <text x="145" y="413" textAnchor="middle" className="text-xs font-bold" fill="#713f12">
              Forwards (TCP):
            </text>
            <text x="55" y="435" className="text-xs" fill="#1e293b">mission_progress: 75%</text>
            <text x="55" y="455" className="text-xs" fill="#1e293b">target_location: "Node5"</text>
            <text x="55" y="475" className="text-xs" fill="#1e293b">current_location: "Node3"</text>
            <line x1="55" y1="490" x2="235" y2="490" stroke="#d97706" strokeWidth="1" strokeDasharray="3,2"/>
            <text x="55" y="507" className="text-xs italic" fill="#16a34a">✓ Logs messages</text>
          </g>
          
        </svg>
      );      

  const RoutingDiagram = () => (
    <svg viewBox="0 0 1000 750" className="w-full h-full">
      {/* Title */}
      <text
        x="500"
        y="30"
        textAnchor="middle"
        className="text-xl font-bold"
        fill="#1f2937"
      >
        Multi-Criteria Route Optimization Example
      </text>
  
     
  
      {/* Comparison Table */}
      <g id="vehicle-comparison">
        <rect
          x="50"
          y="320"
          width="900"
          height="400"
          rx="8"
          fill="#f8fafc"
          stroke="#cbd5e1"
          strokeWidth="2"
        />
        <text
          x="500"
          y="350"
          textAnchor="middle"
          className="font-semibold text-base"
          fill="#1f2937"
        >
          Route Comparison: Node7 → Node4
        </text>
  
        {/* Header row */}
        <rect
          x="50"
          y="370"
          width="900"
          height="60"
          fill="#e2e8f0"
          stroke="#e2e8f0"
          strokeWidth="1.5"
        />
  
        {/* 4 equal columns */}
        {[
          { x: 150, color: "#334155" },
          { x: 325, title: "Vehicle 1", subtitle: "Distance Priority", color: "#1e3a8a" },
          { x: 575, title: "Vehicle 2", subtitle: "Carbon Priority", color: "#047857" },
          { x: 825, title: "Vehicle 3", subtitle: "Cost Priority", color: "#b45309" },
        ].map((col, i) => (
          <g key={i}>
            <text
              x={col.x}
              y="395"
              textAnchor="middle"
              className="font-semibold text-sm"
              fill={col.color}
            >
              {col.title}
            </text>
            <text
              x={col.x}
              y="412"
              textAnchor="middle"
              className="text-xs"
              fill={col.color}
            >
              {col.subtitle}
            </text>
          </g>
        ))}
  
        {/* Column dividers */}
        <line x1="200" y1="370" x2="200" y2="720" stroke="#cbd5e1" strokeWidth="1.5" />
        <line x1="450" y1="370" x2="450" y2="720" stroke="#cbd5e1" strokeWidth="1.5" />
        <line x1="700" y1="370" x2="700" y2="720" stroke="#cbd5e1" strokeWidth="1.5" />
  
        {/* Row labels */}
        {[
          { label: "Path", y: 470 },
          { label: "Distance", y: 520 },
          { label: "Carbon", y: 570 },
          { label: "Cost", y: 620 },
          { label: "Speed", y: 670 },
          { label: "Time", y: 720 },
        ].map((row, i) => (
          <g key={i}>
            <line
              x1="50"
              y1={row.y - 40}
              x2="950"
              y2={row.y - 40}
              stroke="#e2e8f0"
              strokeWidth="1.5"
            />
            <text
              x="125"
              y={row.y - 10}
              textAnchor="middle"
              className="text-sm font-semibold"
              fill="#1f2937"
            >
              {row.label}
            </text>
          </g>
        ))}
  
        {/* Vehicle data */}
        {/* Vehicle 1 - Distance Priority */}
        <text x="325" y="460" textAnchor="middle" className="text-sm" fill="#1e293b">
          Node 7→1→4
        </text>
        <text x="325" y="510" textAnchor="middle" className="text-sm font-semibold" fill="#10b981">
          269.92 units ✓
        </text>
        <text x="325" y="560" textAnchor="middle" className="text-sm" fill="#64748b">
          249.12 kg CO₂
        </text>
        <text x="325" y="610" textAnchor="middle" className="text-sm" fill="#64748b">
          $789.24
        </text>
        <text x="325" y="660" textAnchor="middle" className="text-sm" fill="#64748b">
          35 units/time
        </text>
        <text x="325" y="710" textAnchor="middle" className="text-sm font-bold" fill="#3b82f6">
          7.71 time units
        </text>
  
        {/* Vehicle 2 - Carbon Priority */}
        <text x="575" y="460" textAnchor="middle" className="text-sm" fill="#1e293b">
          Node 7→1→4
        </text>
        <text x="575" y="510" textAnchor="middle" className="text-sm" fill="#64748b">
          269.92 units
        </text>
        <text x="575" y="560" textAnchor="middle" className="text-sm font-semibold" fill="#10b981">
          249.12 kg CO₂ ✓
        </text>
        <text x="575" y="610" textAnchor="middle" className="text-sm" fill="#64748b">
          $789.24
        </text>
        <text x="575" y="660" textAnchor="middle" className="text-sm" fill="#64748b">
          45 units/time
        </text>
        <text x="575" y="710" textAnchor="middle" className="text-sm font-bold" fill="#3b82f6">
          6.00 time units
        </text>
  
        {/* Vehicle 3 - Cost Priority */}
        <text x="825" y="460" textAnchor="middle" className="text-sm" fill="#1e293b">
          Node 7→5→1→2→4
        </text>
        <text x="825" y="510" textAnchor="middle" className="text-sm" fill="#64748b">
          435.41 units
        </text>
        <text x="825" y="560" textAnchor="middle" className="text-sm" fill="#64748b">
          546.20 kg CO₂
        </text>
        <text x="825" y="610" textAnchor="middle" className="text-sm font-semibold" fill="#10b981">
          $159.97 ✓
        </text>
        <text x="825" y="660" textAnchor="middle" className="text-sm" fill="#64748b">
          50 units/time
        </text>
        <text x="825" y="710" textAnchor="middle" className="text-sm font-bold" fill="#3b82f6">
          8.71 time units
        </text>
      </g>
    </svg>
  );

  return (
    <div className="w-full h-screen bg-gray-50 p-6 overflow-hidden">
      <div className="max-w-7xl mx-auto h-full flex flex-col">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Digital Twin Multi-Agent System Diagrams
        </h1>

        {/* ---------- Tabs ---------- */}
        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200">
          {[
            { id: "architecture", label: "System Architecture" },
            { id: "protocol-phase1", label: "Protocol: Proposal & Assignment" },
            { id: "protocol-phase2", label: "Protocol: Execution & Completion" },
            { id: "dataflow", label: "Data Transformation" },
            { id: "routing", label: "Routing Example" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ---------- Diagram Container ---------- */}
        <div className="flex-1 bg-white rounded-lg shadow-lg p-6 overflow-auto">
          {activeTab === "architecture" && <ArchitectureDiagram />}
          {activeTab === "protocol-phase1" && <ProtocolDiagramPhase1 />}
          {activeTab === "protocol-phase2" && <ProtocolDiagramPhase2 />}
          {activeTab === "dataflow" && <DataFlowDiagram />}
          {activeTab === "routing" && <RoutingDiagram />}
        </div>

        {/* ---------- Footer Note ---------- */}
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">FIPA Compliant Protocol:</span> The
            interaction follows Contract Net Protocol standards with proper
            message performatives (cfp, propose, refuse, accept-proposal, reject,
            inform-done) and decision points.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SystemDiagrams;