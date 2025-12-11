import pytest

from app.models.graph import Graph, GraphEdge, GraphNode, NodeData, NodeType, Position


@pytest.mark.asyncio
class TestCanvaPipeline:
    """Integration tests for complete Canva pipeline."""

    async def test_create_graph_with_all_new_nodes(self):
        """Test creating a graph with all new node types."""
        nodes = [
            GraphNode(
                id="start-1",
                type="custom",
                position=Position(x=0, y=0),
                data=NodeData(
                    label="Start",
                    node_type=NodeType.START,
                    config={},
                ),
            ),
            GraphNode(
                id="input-text-1",
                type="custom",
                position=Position(x=0, y=100),
                data=NodeData(
                    label="Text Input",
                    node_type=NodeType.INPUT_TEXT,
                    config={
                        "placeholder": "Enter text",
                        "required": True,
                    },
                ),
            ),
            GraphNode(
                id="llm-transform-1",
                type="custom",
                position=Position(x=0, y=200),
                data=NodeData(
                    label="LLM Transform",
                    node_type=NodeType.LLM_TRANSFORM,
                    config={
                        "provider": "openai",
                        "model": "gpt-4o",
                        "enableVision": False,
                        "temperature": 0.7,
                        "maxTokens": 1000,
                    },
                ),
            ),
            GraphNode(
                id="canva-1",
                type="custom",
                position=Position(x=0, y=300),
                data=NodeData(
                    label="Canva MCP",
                    node_type=NodeType.CANVA_MCP,
                    config={
                        "operation": "create",
                        "outputFormat": "pdf",
                    },
                ),
            ),
            GraphNode(
                id="export-1",
                type="custom",
                position=Position(x=0, y=400),
                data=NodeData(
                    label="Export",
                    node_type=NodeType.OUTPUT_EXPORT,
                    config={
                        "outputType": "pdf",
                        "downloadAutomatically": True,
                    },
                ),
            ),
            GraphNode(
                id="end-1",
                type="custom",
                position=Position(x=0, y=500),
                data=NodeData(
                    label="End",
                    node_type=NodeType.END,
                    config={},
                ),
            ),
        ]

        edges = [
            GraphEdge(id="e1", source="start-1", target="input-text-1"),
            GraphEdge(id="e2", source="input-text-1", target="llm-transform-1"),
            GraphEdge(id="e3", source="llm-transform-1", target="canva-1"),
            GraphEdge(id="e4", source="canva-1", target="export-1"),
            GraphEdge(id="e5", source="export-1", target="end-1"),
        ]

        graph = Graph(
            name="Canva Pipeline Test",
            description="Test pipeline with input -> LLM -> Canva -> Export",
            nodes=nodes,
            edges=edges,
        )

        assert len(graph.nodes) == 6
        assert len(graph.edges) == 5
        assert graph.name == "Canva Pipeline Test"

        node_types = [n.data.node_type for n in graph.nodes]
        assert NodeType.START in node_types
        assert NodeType.INPUT_TEXT in node_types
        assert NodeType.LLM_TRANSFORM in node_types
        assert NodeType.CANVA_MCP in node_types
        assert NodeType.OUTPUT_EXPORT in node_types
        assert NodeType.END in node_types

    async def test_graph_with_image_input_and_vision(self):
        """Test graph with image input and vision-enabled LLM."""
        nodes = [
            GraphNode(
                id="start-1",
                type="custom",
                position=Position(x=0, y=0),
                data=NodeData(
                    label="Start",
                    node_type=NodeType.START,
                    config={},
                ),
            ),
            GraphNode(
                id="input-image-1",
                type="custom",
                position=Position(x=0, y=100),
                data=NodeData(
                    label="Image Input",
                    node_type=NodeType.INPUT_IMAGE,
                    config={
                        "allowUpload": True,
                        "allowUrl": True,
                        "maxFileSizeMB": 10,
                    },
                ),
            ),
            GraphNode(
                id="llm-vision-1",
                type="custom",
                position=Position(x=0, y=200),
                data=NodeData(
                    label="Vision LLM",
                    node_type=NodeType.LLM_TRANSFORM,
                    config={
                        "provider": "openai",
                        "model": "gpt-4o",
                        "enableVision": True,
                        "imageDetail": "high",
                    },
                ),
            ),
            GraphNode(
                id="canva-1",
                type="custom",
                position=Position(x=0, y=300),
                data=NodeData(
                    label="Canva",
                    node_type=NodeType.CANVA_MCP,
                    config={"operation": "create"},
                ),
            ),
            GraphNode(
                id="end-1",
                type="custom",
                position=Position(x=0, y=400),
                data=NodeData(
                    label="End",
                    node_type=NodeType.END,
                    config={},
                ),
            ),
        ]

        edges = [
            GraphEdge(id="e1", source="start-1", target="input-image-1"),
            GraphEdge(id="e2", source="input-image-1", target="llm-vision-1"),
            GraphEdge(id="e3", source="llm-vision-1", target="canva-1"),
            GraphEdge(id="e4", source="canva-1", target="end-1"),
        ]

        graph = Graph(
            name="Vision Pipeline",
            description="Image processing with vision LLM",
            nodes=nodes,
            edges=edges,
        )

        assert len(graph.nodes) == 5
        vision_node = next(
            n for n in graph.nodes if n.id == "llm-vision-1"
        )
        assert vision_node.data.config["enableVision"] is True
        assert vision_node.data.config["imageDetail"] == "high"
