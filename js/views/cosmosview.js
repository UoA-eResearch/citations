// Shared 2D/3D network view — cosmos.gl (GPU force layout & rendering).
// The 3D mode uses the vendored dev build's `spaceDimensions: 3` (orbit camera:
// drag to rotate, scroll to zoom); 2D is the classic pan/zoom plane.
// Loaded as a UMD bundle (global `Cosmos`) from vendor/cosmos-gl/cosmos.min.js.

import { nodeTooltipHTML, showTooltip, hideTooltip } from "../ui.js";

const SPACE = 4096;

function hexToFloats(hex, alpha = 1) {
    const n = parseInt(hex.slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255, alpha];
}

export function createCosmosView(container, { dimensions, onNodeClick }) {
    let graph = null;
    let nodes = [];
    let lastMouse = [0, 0];

    container.addEventListener("mousemove", e => {
        lastMouse = [e.clientX, e.clientY];
    });

    function ensure() {
        if (graph) return graph;
        graph = new Cosmos.Graph(container, {
            spaceDimensions: dimensions,
            spaceSize: SPACE,
            backgroundColor: "#0d0d0d",
            enableDrag: false,
            fitViewOnInit: true,
            fitViewDelay: 1500,
            scalePointsOnZoom: true,
            renderHoveredPointRing: true,
            hoveredPointRingColor: "#d95926",
            ...(dimensions === 3 ? {
                pointSphereShading: true,
                pointDepthFade: 0.1,
                cameraFov: 55,
            } : {}),
            simulationFriction: 0.85,
            simulationGravity: 0.05,
            simulationCenter: 0.3,
            simulationRepulsion: 1.5,
            simulationLinkSpring: 0.8,
            simulationLinkDistance: 15,
            simulationDecay: 6000,
            onClick: index => {
                if (index !== undefined && index !== null && nodes[index]) {
                    try {
                        graph.zoomToPointByIndex(index, 700, 4);
                    } catch { /* fly-to is best-effort */ }
                    onNodeClick(nodes[index]);
                }
            },
            onPointMouseOver: index => {
                if (index !== undefined && index !== null && nodes[index]) {
                    showTooltip(nodeTooltipHTML(nodes[index]), lastMouse[0], lastMouse[1]);
                }
            },
            onPointMouseOut: () => hideTooltip(),
        });
        return graph;
    }

    function applyStyle(colorOf, sizeOf) {
        const colors = new Float32Array(nodes.length * 4);
        const sizes = new Float32Array(nodes.length);
        nodes.forEach((n, i) => {
            const [r, g, b, a] = hexToFloats(colorOf(n));
            colors[i * 4] = r;
            colors[i * 4 + 1] = g;
            colors[i * 4 + 2] = b;
            colors[i * 4 + 3] = a;
            sizes[i] = sizeOf(n) * 2;
        });
        graph.setPointColors(colors);
        graph.setPointSizes(sizes);
    }

    return {
        async update({ nodes: newNodes, links, colorOf, sizeOf }) {
            const g = ensure();
            nodes = newNodes;
            const index = new Map(nodes.map((n, i) => [n.id, i]));
            // Start compact near the centre so repulsion unfolds the layout on screen.
            const positions = new Float32Array(nodes.length * dimensions);
            const centre = SPACE / 2;
            const spread = dimensions === 3 ? SPACE / 8 : SPACE / 4;
            for (let i = 0; i < nodes.length * dimensions; i++) {
                positions[i] = centre + (Math.random() - 0.5) * 2 * spread;
            }
            const linkPairs = [];
            const linkWidths = [];
            for (const l of links) {
                const s = index.get(typeof l.source === "object" ? l.source.id : l.source);
                const t = index.get(typeof l.target === "object" ? l.target.id : l.target);
                if (s !== undefined && t !== undefined) {
                    linkPairs.push(s, t);
                    linkWidths.push(Math.min(5, Math.sqrt(l.weight || 1)));
                }
            }
            g.setPointPositions(positions, { dimensions });
            g.setLinks(new Float32Array(linkPairs));
            const linkColors = new Float32Array((linkPairs.length / 2) * 4);
            for (let i = 0; i < linkPairs.length / 2; i++) {
                linkColors[i * 4] = 1;
                linkColors[i * 4 + 1] = 1;
                linkColors[i * 4 + 2] = 1;
                linkColors[i * 4 + 3] = 0.3;
            }
            g.setLinkColors(linkColors);
            g.setLinkWidths(new Float32Array(linkWidths));
            applyStyle(colorOf, sizeOf);
            g.render(1);
            setTimeout(() => {
                try {
                    g.fitView(600);
                } catch { /* fitViewOnInit already handled it */ }
            }, 4000);
        },
        restyle({ colorOf, sizeOf }) {
            if (!graph || !nodes.length) return;
            applyStyle(colorOf, sizeOf);
            graph.render();
        },
        resize() { /* cosmos observes its container */ },
    };
}
