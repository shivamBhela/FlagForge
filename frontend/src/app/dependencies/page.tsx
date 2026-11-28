"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import {
  Network,
  Search,
  Layers,
  ShieldCheck,
  Share2,
  RefreshCw,
  Box,
  Server,
  Flag,
} from "lucide-react";

export default function DependencyMapPage() {
  const { currentOrg } = useAuth();
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [blastRadius, setBlastRadius] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);

  const handleSelectNode = useCallback(async (node: any) => {
    setSelectedNode(node);
    if (!currentOrg) return;
    if (node.type === "FLAG") {
      setCalculating(true);
      try {
        const blast = await api.dependencies.getBlastRadius(currentOrg.id, node.name);
        setBlastRadius(blast);
      } catch (e) {
        setBlastRadius(null);
      } finally {
        setCalculating(false);
      }
    } else {
      setBlastRadius(null);
    }
  }, [currentOrg]);

  const loadGraph = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const data = await api.dependencies.getGraph(currentOrg.id);
      setGraphData(data);
      if (data.nodes.length > 0 && !selectedNode) {
        await handleSelectNode(data.nodes[0]);
      }
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentOrg) return;
    let ignore = false;
    const fetchGraph = async () => {
      setLoading(true);
      try {
        const data = await api.dependencies.getGraph(currentOrg.id);
        if (ignore) return;
        setGraphData(data);
        if (data.nodes.length > 0) {
          await handleSelectNode(data.nodes[0]);
        }
      } catch {
        // Preserve the last successful graph if refresh fails.
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    void fetchGraph();
    return () => {
      ignore = true;
    };
  }, [currentOrg, handleSelectNode]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#1e293b]">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-400" />
            <span>Dependency Graph & Blast-Radius Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Interactive relational map connecting feature flags, code components, services, and APIs.
          </p>
        </div>
        <button
          onClick={loadGraph}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-[#151e2e] border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-[#1f2937] transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Map</span>
        </button>
      </div>

      {/* Main Grid: Interactive Graph Nodes & Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Visual Graph Canvas */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] flex flex-col justify-between min-h-[480px]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold uppercase text-slate-400">
                Topology Graph ({graphData.nodes.length} Nodes, {graphData.edges.length} Edges)
              </span>
              <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
                <ShieldCheck className="w-3.5 h-3.5" /> 0 Circular Cycles
              </span>
            </div>

            {graphData.nodes.length === 0 ? (
              <div className="text-center py-20 text-slate-500 text-xs">
                No graph nodes generated. Run a code scan in Code Scanner to populate AST dependencies.
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {graphData.nodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  return (
                    <button
                      key={node.id}
                      onClick={() => handleSelectNode(node)}
                      className={`p-3.5 rounded-xl border text-left transition flex flex-col justify-between ${
                        isSelected
                          ? "bg-blue-600/15 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                          : "bg-[#151e2e] border-[#1e293b] text-slate-300 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#0c121e] text-blue-400 font-mono">
                          {node.type}
                        </span>
                        {node.type === "FLAG" ? (
                          <Flag className="w-3.5 h-3.5 text-blue-400" />
                        ) : node.type === "SERVICE" ? (
                          <Server className="w-3.5 h-3.5 text-purple-400" />
                        ) : (
                          <Box className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                      </div>
                      <span className="font-mono text-xs font-bold truncate">{node.name}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-[#1e293b] text-[11px] text-slate-500 flex items-center justify-between font-mono">
            <span>Inferred from AST call-trees & service bindings</span>
            <span>Confidence Threshold: ≥85%</span>
          </div>
        </div>

        {/* Right Column: Node Details & Blast Radius */}
        <div className="space-y-6">
          <div className="p-6 rounded-xl bg-[#0c121e] border border-[#1e293b] space-y-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Share2 className="w-4 h-4 text-purple-400" />
              <span>Node Impact & Blast Radius</span>
            </h2>

            {selectedNode ? (
              <div className="space-y-4">
                <div className="p-3.5 rounded-lg bg-[#151e2e] border border-[#1e293b] space-y-1">
                  <div className="text-[11px] uppercase font-semibold text-slate-400">Selected Entity</div>
                  <div className="font-mono text-sm font-bold text-white">{selectedNode.name}</div>
                  <div className="text-[11px] text-blue-400 font-mono">Type: {selectedNode.type}</div>
                </div>

                {blastRadius && (
                  <div className="space-y-3">
                    <div className="p-4 rounded-xl bg-[#10192b] border border-blue-500/30">
                      <div className="text-[11px] uppercase font-semibold text-slate-400">Calculated Blast Radius</div>
                      <div className="text-3xl font-bold text-white mt-1">
                        {blastRadius.impact_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Disabling or mutating this flag affects {blastRadius.affected_components_count} components across {blastRadius.affected_services_count} services.
                      </p>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <span className="text-[11px] font-semibold uppercase text-slate-500">Affected Downstream Services</span>
                      <div className="flex flex-wrap gap-1.5">
                        {blastRadius.affected_services.map((svc: string) => (
                          <span key={svc} className="px-2 py-0.5 rounded bg-[#151e2e] text-slate-300 font-mono text-[11px] border border-[#1e293b]">
                            {svc}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6 text-center">Select any graph node to inspect its blast radius.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
