#!/usr/bin/env python3
"""
Unit Tests for Dataset Creation Module
=======================================

Run tests with: python -m pytest tests_dataset_creation.py -v
"""

import unittest
import tempfile
import json
from pathlib import Path
from experiments.dataset_creator import (
    Node, Edge, Service, Query, DatasetConfig,
    NodeGenerator, EdgeGenerator, QueryGenerator,
    DatasetValidator, DatasetCreator
)


class TestDataStructures(unittest.TestCase):
    """Test data structure classes."""
    
    def test_node_creation(self):
        """Test Node dataclass."""
        node = Node(1, 10.5, 20.3)
        self.assertEqual(node.node_id, 1)
        self.assertEqual(node.x, 10.5)
        self.assertEqual(node.y, 20.3)
    
    def test_node_distance(self):
        """Test Euclidean distance calculation."""
        node1 = Node(1, 0.0, 0.0)
        node2 = Node(2, 3.0, 4.0)
        distance = node1.euclidean_distance(node2)
        self.assertAlmostEqual(distance, 5.0, places=5)
    
    def test_node_csv_format(self):
        """Test node CSV output."""
        node = Node(0, -121.904, 41.975)
        csv_row = node.to_csv_row()
        self.assertIn('0', csv_row)
        self.assertIn('-121.904', csv_row)
        self.assertIn('41.975', csv_row)
    
    def test_edge_creation(self):
        """Test Edge dataclass."""
        costs = [0.1, 0.11, 0.12, 0.13]
        edge = Edge(1, 2, costs)
        self.assertEqual(edge.source, 1)
        self.assertEqual(edge.destination, 2)
        self.assertEqual(len(edge.costs), 4)
    
    def test_edge_csv_format(self):
        """Test edge CSV output."""
        costs = [0.1, 0.2, 0.3, 0.4]
        edge = Edge(5, 10, costs)
        csv_row = edge.to_csv_row()
        self.assertIn('5', csv_row)
        self.assertIn('10', csv_row)
        self.assertIn('0.1', csv_row)
    
    def test_service_creation(self):
        """Test Service dataclass."""
        service = Service(
            service_id=1,
            pickup_node=10,
            delivery_node=20,
            demand=3,
            pickup_start=540,
            pickup_end=600,
            delivery_start=650,
            delivery_end=750
        )
        self.assertEqual(service.service_id, 1)
        self.assertEqual(service.demand, 3)
    
    def test_service_query_format(self):
        """Test service query file format."""
        service = Service(1, 10, 20, 3, 540, 600, 650, 750)
        query_row = service.to_query_row()
        self.assertIn('10,20', query_row)
        self.assertIn('[540,600]', query_row)
        self.assertIn('[650,750]', query_row)
        self.assertIn('3', query_row)
    
    def test_query_creation(self):
        """Test Query dataclass."""
        services = [
            Service(1, 10, 20, 2, 540, 600, 650, 750),
            Service(2, 30, 40, 3, 600, 660, 700, 800)
        ]
        query = Query(query_id=1, depot_node=1, capacity=10, services=services)
        self.assertEqual(query.query_id, 1)
        self.assertEqual(query.capacity, 10)
        self.assertEqual(len(query.services), 2)
    
    def test_query_metadata(self):
        """Test query metadata generation."""
        services = [Service(1, 10, 20, 2, 540, 600, 650, 750)]
        query = Query(1, 1, 10, services)
        metadata = query.to_metadata()
        self.assertEqual(metadata['query_id'], 1)
        self.assertEqual(metadata['n_requests'], 1)
        self.assertIn('demand_range', metadata)


class TestNodeGenerator(unittest.TestCase):
    """Test NodeGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = DatasetConfig(num_nodes=50, node_seed=42)
        self.generator = NodeGenerator(self.config)
    
    def test_uniform_random_generation(self):
        """Test uniform random node generation."""
        nodes = self.generator.generate_uniform_random()
        self.assertEqual(len(nodes), 50)
        
        # Check bounds
        for node in nodes.values():
            self.assertGreaterEqual(node.x, self.config.x_bounds[0])
            self.assertLessEqual(node.x, self.config.x_bounds[1])
            self.assertGreaterEqual(node.y, self.config.y_bounds[0])
            self.assertLessEqual(node.y, self.config.y_bounds[1])
    
    def test_clustered_generation(self):
        """Test clustered node generation."""
        nodes = self.generator.generate_clustered(num_clusters=3)
        self.assertEqual(len(nodes), 50)
        
        # Check bounds
        for node in nodes.values():
            self.assertGreaterEqual(node.x, self.config.x_bounds[0])
            self.assertLessEqual(node.x, self.config.x_bounds[1])
    
    def test_node_file_save(self):
        """Test saving nodes to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nodes = self.generator.generate_uniform_random()
            output_file = Path(tmpdir) / 'nodes.txt'
            
            self.generator.save_to_file(output_file)
            
            self.assertTrue(output_file.exists())
            with open(output_file, 'r') as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 50)
    
    def test_node_file_load(self):
        """Test loading nodes from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save nodes
            nodes = self.generator.generate_uniform_random()
            output_file = Path(tmpdir) / 'nodes.txt'
            self.generator.save_to_file(output_file)
            
            # Load nodes
            gen2 = NodeGenerator(self.config)
            loaded_nodes = gen2.load_from_file(output_file)
            
            self.assertEqual(len(loaded_nodes), 50)
            for node_id in nodes.keys():
                self.assertAlmostEqual(
                    nodes[node_id].x,
                    loaded_nodes[node_id].x,
                    places=5
                )
    
    def test_reproducibility(self):
        """Test that same seed produces same nodes."""
        nodes1 = self.generator.generate_uniform_random()
        
        gen2 = NodeGenerator(self.config)
        nodes2 = gen2.generate_uniform_random()
        
        for node_id in nodes1.keys():
            self.assertEqual(nodes1[node_id].x, nodes2[node_id].x)
            self.assertEqual(nodes1[node_id].y, nodes2[node_id].y)


class TestEdgeGenerator(unittest.TestCase):
    """Test EdgeGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = DatasetConfig(num_nodes=30, edge_seed=42)
        self.node_gen = NodeGenerator(self.config)
        self.nodes = self.node_gen.generate_uniform_random()
        self.edge_gen = EdgeGenerator(self.nodes, self.config)
    
    def test_knn_generation(self):
        """Test k-nearest neighbors edge generation."""
        edges = self.edge_gen.generate_k_nearest_neighbors(k=5)
        self.assertGreater(len(edges), 0)
        
        # Each node should have at most k outgoing edges
        out_degree = {}
        for (source, _), _ in edges.items():
            out_degree[source] = out_degree.get(source, 0) + 1
        
        for source, degree in out_degree.items():
            self.assertLessEqual(degree, 5)
    
    def test_random_edge_generation(self):
        """Test random edge generation."""
        self.config.edge_density = 0.05
        edges = self.edge_gen.generate_random_edges()
        self.assertGreater(len(edges), 0)
        
        # Check all edges are valid
        valid_nodes = set(self.nodes.keys())
        for (source, dest), _ in edges.items():
            self.assertIn(source, valid_nodes)
            self.assertIn(dest, valid_nodes)
            self.assertNotEqual(source, dest)
    
    def test_edge_costs_positive(self):
        """Test that all edge costs are positive."""
        edges = self.edge_gen.generate_k_nearest_neighbors(k=5)
        for edge in edges.values():
            for cost in edge.costs:
                self.assertGreater(cost, 0)
    
    def test_edge_file_save(self):
        """Test saving edges to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            edges = self.edge_gen.generate_k_nearest_neighbors(k=5)
            output_file = Path(tmpdir) / 'edges.txt'
            
            self.edge_gen.save_to_file(output_file)
            
            self.assertTrue(output_file.exists())
            with open(output_file, 'r') as f:
                lines = f.readlines()
            # First line is time series, rest are edges
            self.assertEqual(len(lines) - 1, len(edges))


class TestQueryGenerator(unittest.TestCase):
    """Test QueryGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = DatasetConfig(
            num_nodes=100,
            n_requests=10,
            query_seed=42
        )
        self.node_gen = NodeGenerator(self.config)
        self.nodes = self.node_gen.generate_uniform_random()
        self.query_gen = QueryGenerator(self.nodes, self.config)
    
    def test_single_query_generation(self):
        """Test generating a single query."""
        query = self.query_gen.generate_query(query_id=1)
        self.assertEqual(query.query_id, 1)
        self.assertIn(query.depot_node, self.nodes.keys())
        self.assertEqual(len(query.services), 10)
    
    def test_multiple_queries_generation(self):
        """Test generating multiple queries."""
        queries = self.query_gen.generate_queries(num_queries=5)
        self.assertEqual(len(queries), 5)
        
        for i, query in enumerate(queries):
            self.assertEqual(query.query_id, i)
    
    def test_service_constraints(self):
        """Test that services respect constraints."""
        query = self.query_gen.generate_query(1)
        
        for service in query.services:
            # Time window constraints
            self.assertLess(service.pickup_start, service.pickup_end)
            self.assertLess(service.delivery_start, service.delivery_end)
            self.assertLess(service.pickup_end, service.delivery_start)
            
            # Demand constraints
            self.assertGreaterEqual(service.demand, self.config.demand_min)
            self.assertLessEqual(service.demand, self.config.demand_max)
            
            # Nodes must exist
            self.assertIn(service.pickup_node, self.nodes.keys())
            self.assertIn(service.delivery_node, self.nodes.keys())
    
    def test_query_file_save(self):
        """Test saving queries to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            queries = self.query_gen.generate_queries(num_queries=3)
            output_dir = Path(tmpdir) / 'queries'
            
            self.query_gen.save_queries(queries, output_dir)
            
            self.assertTrue(output_dir.exists())
            query_files = list(output_dir.glob('query_*.txt'))
            self.assertEqual(len(query_files), 3)
            
            meta_files = list(output_dir.glob('query_*_meta.json'))
            self.assertEqual(len(meta_files), 3)


class TestDatasetValidator(unittest.TestCase):
    """Test DatasetValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DatasetValidator()
    
    def test_node_validation_valid(self):
        """Test validation of valid nodes."""
        nodes = {
            0: Node(0, 0.0, 0.0),
            1: Node(1, 10.0, 10.0),
            2: Node(2, 20.0, 20.0)
        }
        self.assertTrue(self.validator.validate_nodes(nodes))
    
    def test_node_validation_duplicate_ids(self):
        """Test validation catches duplicate node IDs."""
        nodes = {
            0: Node(0, 0.0, 0.0),
            1: Node(1, 10.0, 10.0),
            2: Node(1, 20.0, 20.0)  # Duplicate ID
        }
        self.validator.errors = []
        self.assertFalse(self.validator.validate_nodes(nodes))
    
    def test_edge_validation_valid(self):
        """Test validation of valid edges."""
        nodes = {
            0: Node(0, 0.0, 0.0),
            1: Node(1, 10.0, 10.0)
        }
        edges = {
            (0, 1): Edge(0, 1, [1.0, 1.1, 1.2, 1.3]),
            (1, 0): Edge(1, 0, [1.0, 1.1, 1.2, 1.3])
        }
        self.validator.errors = []
        self.assertTrue(self.validator.validate_edges(edges, nodes))
    
    def test_edge_validation_nonexistent_node(self):
        """Test validation catches nonexistent nodes."""
        nodes = {0: Node(0, 0.0, 0.0)}
        edges = {
            (0, 5): Edge(0, 5, [1.0, 1.1, 1.2, 1.3])  # Node 5 doesn't exist
        }
        self.validator.errors = []
        self.assertFalse(self.validator.validate_edges(edges, nodes))


class TestDatasetCreator(unittest.TestCase):
    """Test DatasetCreator orchestrator."""
    
    def test_create_synthetic_dataset(self):
        """Test creating complete synthetic dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DatasetConfig(
                num_nodes=50,
                num_queries=3,
                node_seed=42,
                edge_seed=42,
                query_seed=42
            )
            
            creator = DatasetCreator(config, Path(tmpdir))
            nodes, edges = creator.create_synthetic_dataset()
            
            self.assertEqual(len(nodes), 50)
            self.assertGreater(len(edges), 0)
    
    def test_create_queries(self):
        """Test creating queries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DatasetConfig(
                num_nodes=50,
                num_queries=3,
                node_seed=42
            )
            
            creator = DatasetCreator(config, Path(tmpdir))
            nodes, _ = creator.create_synthetic_dataset()
            queries = creator.create_queries(nodes, num_queries=3)
            
            self.assertEqual(len(queries), 3)
    
    def test_complete_dataset_creation(self):
        """Test creating complete dataset with all components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DatasetConfig(
                num_nodes=30,
                num_queries=2,
                node_seed=42,
                edge_seed=42,
                query_seed=42
            )
            
            creator = DatasetCreator(config, Path(tmpdir))
            creator.create_complete_dataset()
            
            output_dir = Path(tmpdir)
            self.assertTrue((output_dir / 'nodes.txt').exists())
            self.assertTrue((output_dir / 'edges.txt').exists())
            self.assertTrue((output_dir / 'queries').exists())
            
            query_files = list((output_dir / 'queries').glob('query_*.txt'))
            self.assertEqual(len(query_files), 2)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_end_to_end_dataset_creation(self):
        """Test end-to-end dataset creation and validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DatasetConfig(
                num_nodes=50,
                num_queries=5,
                node_seed=42,
                edge_seed=42,
                query_seed=42
            )
            
            creator = DatasetCreator(config, Path(tmpdir))
            creator.create_complete_dataset()
            
            # Load and validate
            validator = DatasetValidator()
            
            # Count files
            output_dir = Path(tmpdir)
            query_files = list(output_dir.glob('queries/query_*.txt'))
            self.assertEqual(len(query_files), 5)
            
            # Validate first query file format
            with open(query_files[0], 'r') as f:
                lines = f.readlines()
            self.assertTrue(lines[0].startswith('D '))
            self.assertTrue(lines[1].startswith('C '))


if __name__ == '__main__':
    unittest.main()
