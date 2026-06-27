import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network/standalone';
import { documentsApi } from '../../../api/documents';
import './KnowledgeGraphViewer.css';

export default function KnowledgeGraphViewer() {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSubgraph, setShowSubgraph] = useState(false); // по умолчанию скрыты
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await documentsApi.graph();
        if (!mounted) return;
        if (data && data.nodes && data.edges) {
          setGraphData(data);
          setTimeout(() => {
            if (mounted) renderGraph(data.nodes, data.edges, showSubgraph);
          }, 100);
        } else {
          setError('Нет данных для отображения');
        }
      } catch (err) {
        if (mounted) {
          setError('Ошибка загрузки графа');
          console.error(err);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchData();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      renderGraph(graphData.nodes, graphData.edges, showSubgraph);
    }
  }, [showSubgraph, graphData]);

  const renderGraph = (nodes, edges, showSub) => {
    if (!containerRef.current) return;

    // Фильтруем узлы и рёбра
    let filteredNodes = nodes;
    let filteredEdges = edges;
    if (!showSub) {
      const subgraphIds = new Set(
        nodes.filter(n => n.type === 'SUBGRAPH').map(n => n.id)
      );
      filteredNodes = nodes.filter(n => n.type !== 'SUBGRAPH');
      filteredEdges = edges.filter(e =>
        !subgraphIds.has(e.from) && !subgraphIds.has(e.to)
      );
    }

    // Палитра
    const colors = {
      subgraph: '#1a3a5c',   // тёмно-синий
      term: '#3498db',       // синий
      unknown: '#95a5a6',    // серый
    };

    const visNodes = filteredNodes.map(n => {
      const isSubgraph = n.type === 'SUBGRAPH';
      const level = n.level || 0;

      let color, shape, size, fontColor, borderColor;
      if (isSubgraph) {
        color = colors.subgraph;
        shape = 'box';
        size = 40;
        fontColor = 'white';
        borderColor = '#0f2840';
      } else if (n.type === 'TERM') {
        // Чем выше уровень, тем темнее синий (от светлого к тёмному)
        const lightness = 70 - level * 8; // 70, 62, 54, 46
        color = `hsl(210, 70%, ${lightness}%)`;
        shape = 'dot';
        size = 20 + level * 4;
        fontColor = level > 2 ? 'white' : '#1a1a2e';
        borderColor = 'transparent';
      } else {
        color = colors.unknown;
        shape = 'diamond';
        size = 18;
        fontColor = '#1a1a2e';
        borderColor = '#7f8c8d';
      }

      return {
        id: n.id,
        label: n.label || n.id,
        title: `ID: ${n.id}\nТип: ${n.type}\nУровень: ${level}`,
        color: {
          background: color,
          border: borderColor || color,
        },
        shape,
        size,
        font: { size: isSubgraph ? 18 : 14, face: 'Arial', color: fontColor },
        borderWidth: isSubgraph ? 2 : 0,
      };
    });

    const visEdges = filteredEdges.map(e => ({
      from: e.from,
      to: e.to,
      label: e.type,
      arrows: 'to',
      color: e.type === 'link' ? '#2ecc71' : (e.type === 'parent' ? '#e74c3c' : '#f1c40f'),
      font: { size: 12, align: 'middle' },
      smooth: false,
      width: 1.5,
    }));

    const data = { nodes: visNodes, edges: visEdges };
    const options = {
      nodes: {
        shape: 'dot',
        size: 20,
        font: { size: 14, face: 'Arial' },
      },
      edges: {
        smooth: false,
        font: { size: 12, align: 'middle' },
        width: 1.5,
      },
      physics: false,
      interaction: {
        hover: true,
        tooltipDelay: 200,
        navigationButtons: true,
        keyboard: true,
      },
      layout: {
        improvedLayout: true,
        randomSeed: 42,
      },
    };

    if (networkRef.current) {
      networkRef.current.setData(data);
    } else {
      networkRef.current = new Network(containerRef.current, data, options);
    }
  };

  if (loading) return <div className="graph-loading">Загрузка графа знаний...</div>;
  if (error) return <div className="graph-error">{error}</div>;

  return (
    <div className="graph-container">
      <div className="graph-controls">
        <label>
          <input
            type="checkbox"
            checked={showSubgraph}
            onChange={(e) => setShowSubgraph(e.target.checked)}
          />
          Показать документы (SUBGRAPH)
        </label>
        <span className="graph-legend">
          <span className="legend-item">
            <span className="legend-color" style={{ background: '#1a3a5c' }}></span>
            Документ
          </span>
          <span className="legend-item">
            <span className="legend-color" style={{ background: '#3498db' }}></span>
            Термин / Значение
          </span>
          <span className="legend-item">
            <span className="legend-color" style={{ background: '#95a5a6' }}></span>
            UNKNOWN
          </span>
        </span>
      </div>
      <div ref={containerRef} style={{ width: '100%', height: '600px', border: '1px solid #ddd', borderRadius: '8px' }} />
    </div>
  );
}