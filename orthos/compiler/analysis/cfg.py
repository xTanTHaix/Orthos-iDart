"""
Control Flow Graph (CFG) Analysis Module for Orthos Compiler
Builds and analyzes control flow graphs for optimization opportunities
"""

import ast
import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the CFG"""
    ENTRY = "entry"
    BASIC_BLOCK = "basic_block"
    LOOP_HEADER = "loop_header"
    LOOP_EXIT = "loop_exit"
    JUMP = "jump"
    RETURN = "return"
    CALL = "call"
    PHI = "phi"


@dataclass
class BasicBlock:
    """Represents a basic block in the CFG"""
    id: int
    node_type: NodeType = NodeType.BASIC_BLOCK
    instructions: List[str] = field(default_factory=list)
    predecessors: List[int] = field(default_factory=list)
    successors: List[int] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False
    is_loop_header: bool = False
    is_loop_exit: bool = False
    loop_depth: int = 0
    line_number: int = 0
    
    def add_predecessor(self, pred_id: int) -> None:
        """Add predecessor block"""
        if pred_id not in self.predecessors:
            self.predecessors.append(pred_id)
    
    def add_successor(self, succ_id: int) -> None:
        """Add successor block"""
        if succ_id not in self.successors:
            self.successors.append(succ_id)
    
    def get_predecessors(self) -> List['BasicBlock']:
        """Get predecessor blocks"""
        return [self.blocks[pred_id] for pred_id in self.predecessors if pred_id in self.blocks]
    
    def get_successors(self) -> List['BasicBlock']:
        """Get successor blocks"""
        return [self.blocks[succ_id] for succ_id in self.successors if succ_id in self.blocks]
    
    def is_phi_source(self) -> bool:
        """Check if this block is a phi source"""
        return any(pred_id in self.blocks for pred_id in self.predecessors)


@dataclass
class CFG:
    """Control Flow Graph"""
    blocks: Dict[int, BasicBlock] = field(default_factory=dict)
    entry_block: Optional[int] = None
    exit_blocks: List[int] = field(default_factory=list)
    loop_headers: List[int] = field(default_factory=list)
    loop_exits: List[int] = field(default_factory=list)
    dominators: Dict[int, Set[int]] = field(default_factory=dict)
    post_dominators: Dict[int, Set[int]] = field(default_factory=dict)
    dominance_frontier: Dict[int, Set[int]] = field(default_factory=dict)
    
    def add_block(self, block: BasicBlock) -> None:
        """Add a basic block to the CFG"""
        self.blocks[block.id] = block
    
    def set_entry(self, block_id: int) -> None:
        """Set entry block"""
        if block_id in self.blocks:
            self.blocks[block_id].is_entry = True
            self.entry_block = block_id
    
    def set_exit(self, block_id: int) -> None:
        """Set exit block"""
        if block_id in self.blocks:
            self.blocks[block_id].is_exit = True
            if block_id not in self.exit_blocks:
                self.exit_blocks.append(block_id)
    
    def add_edge(self, from_id: int, to_id: int) -> None:
        """Add edge between blocks"""
        if from_id in self.blocks and to_id in self.blocks:
            self.blocks[from_id].add_successor(to_id)
            self.blocks[to_id].add_predecessor(from_id)
    
    def get_entry(self) -> Optional[BasicBlock]:
        """Get entry block"""
        return self.blocks.get(self.entry_block) if self.entry_block else None
    
    def get_exit_blocks(self) -> List[BasicBlock]:
        """Get all exit blocks"""
        return [self.blocks[bid] for bid in self.exit_blocks if bid in self.blocks]
    
    def get_successors(self, block_id: int) -> List[BasicBlock]:
        """Get successors of a block"""
        block = self.blocks.get(block_id)
        return block.get_successors() if block else []
    
    def get_predecessors(self, block_id: int) -> List[BasicBlock]:
        """Get predecessors of a block"""
        block = self.blocks.get(block_id)
        return block.get_predecessors() if block else []
    
    def is_reachable(self, from_id: int, to_id: int) -> bool:
        """Check if to_id is reachable from from_id"""
        if from_id not in self.blocks or to_id not in self.blocks:
            return False
        
        visited: Set[int] = set()
        queue: deque = deque([from_id])
        
        while queue:
            current = queue.popleft()
            if current == to_id:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            for succ_id in self.blocks[current].successors:
                if succ_id not in visited:
                    queue.append(succ_id)
        
        return False
    
    def find_loops(self) -> Dict[int, Set[int]]:
        """Find all loops in the CFG using Tarjan's algorithm"""
        # Simplified loop detection
        loops: Dict[int, Set[int]] = {}
        
        # Find loop headers (blocks with multiple predecessors)
        for block_id, block in self.blocks.items():
            if len(block.predecessors) > 1:
                # Check if it's a loop header
                block.is_loop_header = True
                self.loop_headers.append(block_id)
                
                # Find loop members (blocks that can reach header)
                loop_members = self._find_loop_members(block_id)
                loops[block_id] = loop_members
        
        return loops
    
    def _find_loop_members(self, header_id: int) -> Set[int]:
        """Find all members of a loop"""
        members: Set[int] = set()
        visited: Set[int] = set()
        queue: deque = deque([header_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            members.add(current)
            
            for pred_id in self.blocks[current].predecessors:
                if pred_id not in visited:
                    queue.append(pred_id)
        
        return members
    
    def compute_dominators(self) -> Dict[int, Set[int]]:
        """Compute dominators using iterative dataflow analysis"""
        if self.entry_block is None:
            if 0 in self.blocks:
                self.set_entry(0)
            elif self.blocks:
                self.set_entry(min(self.blocks.keys()))
            else:
                return self.dominators
        
        # Initialize
        all_blocks = set(self.blocks.keys())
        entry = self.entry_block
        
        # Dominators[entry] = {entry}
        # Dominators[others] = all_blocks
        dominators: Dict[int, Set[int]] = {}
        for block_id in all_blocks:
            if block_id == entry:
                dominators[block_id] = {entry}
            else:
                dominators[block_id] = set(all_blocks)
        
        # Iterate until fixed point
        changed = True
        while changed:
            changed = False
            for block_id in all_blocks:
                if block_id == entry:
                    continue
                
                block = self.blocks[block_id]
                if not block.predecessors:
                    continue
                
                # New dominators = intersection of all predecessors' dominators + self
                new_doms = set(all_blocks)
                for pred_id in block.predecessors:
                    if pred_id in dominators:
                        new_doms &= dominators[pred_id]
                
                new_doms.add(block_id)
                
                if new_doms != dominators[block_id]:
                    dominators[block_id] = new_doms
                    changed = True
        
        self.dominators = dominators
        return self.dominators
    
    def compute_post_dominators(self) -> Dict[int, Set[int]]:
        """Compute post-dominators (reverse CFG)"""
        # Simplified: compute on reversed graph
        # For now, use symmetry approximation
        self.post_dominators = {}
        for block_id, doms in self.dominators.items():
            self.post_dominators[block_id] = doms.copy()
        return self.post_dominators
    
    def compute_dominance_frontier(self) -> Dict[int, Set[int]]:
        """Compute dominance frontier for each block"""
        self.dominance_frontier = {}
        
        for block_id, block in self.blocks.items():
            if not block.predecessors:
                continue
            
            # Dominance frontier = union of (dom(n) - dom(p)) for all predecessors p
            frontier: Set[int] = set()
            
            for pred_id in block.predecessors:
                if pred_id in self.dominators:
                    dom_pred = self.dominators[pred_id]
                    dom_block = self.dominators[block_id]
                    frontier |= (dom_pred - dom_block)
            
            if frontier:
                self.dominance_frontier[block_id] = frontier
        return self.dominance_frontier
    
    def get_dominator(self, block_id: int) -> Optional[int]:
        """Get immediate dominator of a block"""
        if block_id not in self.dominators:
            return None
        
        doms = self.dominators[block_id]
        if len(doms) <= 1:
            return None
        
        # Immediate dominator is the one with smallest set (excluding self)
        for other_id, other_doms in self.dominators.items():
            if other_id != block_id and other_doms.issubset(doms):
                return other_id
        
        return None
    
    def get_loop_depth(self, block_id: int) -> int:
        """Get loop depth of a block"""
        depth = 0
        current = block_id
        
        while current:
            block = self.blocks.get(current)
            if not block or not block.is_loop_header:
                break
            depth += 1
            current = self.get_dominator(current)
        
        return depth
    
    def get_basic_blocks(self) -> List[BasicBlock]:
        """Get all basic blocks"""
        return list(self.blocks.values())
    
    def get_linear_blocks(self) -> List[BasicBlock]:
        """Get linear blocks (no control flow)"""
        linear = []
        for block in self.blocks.values():
            if len(block.successors) == 1 and len(block.predecessors) == 1:
                linear.append(block)
        return linear
    
    def get_conditional_blocks(self) -> List[BasicBlock]:
        """Get conditional blocks (branching)"""
        conditional = []
        for block in self.blocks.values():
            if len(block.successors) > 1:
                conditional.append(block)
        return conditional
    
    def get_jumps(self) -> List[BasicBlock]:
        """Get jump blocks"""
        jumps = []
        for block in self.blocks.values():
            if block.node_type == NodeType.JUMP:
                jumps.append(block)
        return jumps
    
    def get_returns(self) -> List[BasicBlock]:
        """Get return blocks"""
        returns = []
        for block in self.blocks.values():
            if block.node_type == NodeType.RETURN:
                returns.append(block)
        return returns
    
    def get_phi_sources(self) -> List[BasicBlock]:
        """Get phi source blocks"""
        sources = []
        for block in self.blocks.values():
            if block.is_phi_source():
                sources.append(block)
        return sources
    
    def to_dict(self) -> Dict:
        """Serialize CFG to dictionary"""
        return {
            "entry_block": self.entry_block,
            "exit_blocks": self.exit_blocks,
            "loop_headers": self.loop_headers,
            "loop_exits": self.loop_exits,
            "num_blocks": len(self.blocks),
            "num_edges": sum(len(b.successors) for b in self.blocks.values()),
            "dominators": {str(k): list(v) for k, v in self.dominators.items()},
            "blocks": {
                bid: {
                    "type": b.node_type.value,
                    "instructions": b.instructions,
                    "predecessors": b.predecessors,
                    "successors": b.successors,
                    "is_entry": b.is_entry,
                    "is_exit": b.is_exit,
                    "is_loop_header": b.is_loop_header,
                    "is_loop_exit": b.is_loop_exit,
                    "loop_depth": b.loop_depth,
                    "line_number": b.line_number
                }
                for bid, b in self.blocks.items()
            }
        }


class ASTCFGBuilder:
    """Constructs a CFG from Python AST structures."""
    def __init__(self, cfg: CFG):
        self.cfg = cfg
        self._next_id = 0

    def _new_block(self, node_type: NodeType = NodeType.BASIC_BLOCK, line_number: int = 1) -> BasicBlock:
        block = BasicBlock(id=self._next_id, node_type=node_type, line_number=line_number)
        self._next_id += 1
        self.cfg.add_block(block)
        return block

    def build_from_ast(self, tree: ast.AST) -> CFG:
        entry = self._new_block(NodeType.ENTRY, line_number=getattr(tree, 'lineno', 1))
        self.cfg.set_entry(entry.id)
        
        stmts = []
        if isinstance(tree, ast.Module):
            stmts = tree.body
        elif isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stmts = tree.body
        elif isinstance(tree, list):
            stmts = tree
        else:
            stmts = [tree]
            
        current = entry
        current = self._build_stmts(stmts, current)
        
        if not self.cfg.exit_blocks:
            exit_blk = self._new_block(NodeType.RETURN, line_number=1000)
            self.cfg.set_exit(exit_blk.id)
            if current and exit_blk.id not in current.successors:
                self.cfg.add_edge(current.id, exit_blk.id)
        elif current and not current.is_exit and not current.successors:
            for exit_id in self.cfg.exit_blocks:
                self.cfg.add_edge(current.id, exit_id)
                
        self.cfg.find_loops()
        self.cfg.compute_dominators()
        self.cfg.compute_post_dominators()
        self.cfg.compute_dominance_frontier()
        return self.cfg

    def _build_stmts(self, stmts: List[ast.AST], current: BasicBlock) -> BasicBlock:
        for stmt in stmts:
            current = self._build_stmt(stmt, current)
        return current

    def _build_stmt(self, stmt: ast.AST, current: BasicBlock) -> BasicBlock:
        lineno = getattr(stmt, 'lineno', current.line_number)
        if isinstance(stmt, ast.If):
            current.instructions.append(f"IF {ast.dump(stmt.test)}")
            then_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            self.cfg.add_edge(current.id, then_blk.id)
            then_end = self._build_stmts(stmt.body, then_blk)
            
            merge_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            if stmt.orelse:
                else_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
                self.cfg.add_edge(current.id, else_blk.id)
                else_end = self._build_stmts(stmt.orelse, else_blk)
                if else_end and not else_end.is_exit:
                    self.cfg.add_edge(else_end.id, merge_blk.id)
            else:
                self.cfg.add_edge(current.id, merge_blk.id)
                
            if then_end and not then_end.is_exit:
                self.cfg.add_edge(then_end.id, merge_blk.id)
                
            return merge_blk

        elif isinstance(stmt, (ast.While, ast.For, ast.AsyncFor)):
            header_blk = self._new_block(NodeType.LOOP_HEADER, line_number=lineno)
            header_blk.is_loop_header = True
            if header_blk.id not in self.cfg.loop_headers:
                self.cfg.loop_headers.append(header_blk.id)
            self.cfg.add_edge(current.id, header_blk.id)
            header_blk.instructions.append(f"LOOP_TEST {type(stmt).__name__}")
            
            body_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            self.cfg.add_edge(header_blk.id, body_blk.id)
            body_end = self._build_stmts(stmt.body, body_blk)
            if body_end and not body_end.is_exit:
                self.cfg.add_edge(body_end.id, header_blk.id)
                
            exit_blk = self._new_block(NodeType.LOOP_EXIT, line_number=lineno)
            exit_blk.is_loop_exit = True
            if exit_blk.id not in self.cfg.loop_exits:
                self.cfg.loop_exits.append(exit_blk.id)
            self.cfg.add_edge(header_blk.id, exit_blk.id)
            return exit_blk

        elif isinstance(stmt, ast.Return):
            current.instructions.append("RETURN")
            current.node_type = NodeType.RETURN
            current.is_exit = True
            self.cfg.set_exit(current.id)
            next_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            return next_blk

        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            current.instructions.append(f"DEF {stmt.name}")
            func_entry = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            self.cfg.add_edge(current.id, func_entry.id)
            func_end = self._build_stmts(stmt.body, func_entry)
            merge_blk = self._new_block(NodeType.BASIC_BLOCK, line_number=lineno)
            if func_end and not func_end.is_exit:
                self.cfg.add_edge(func_end.id, merge_blk.id)
            self.cfg.add_edge(current.id, merge_blk.id)
            return merge_blk

        else:
            current.instructions.append(f"STMT {type(stmt).__name__}")
            return current


class CFGBuilder:
    """Builds CFG from bytecode instructions, AST, or Python source code"""
    
    def __init__(self):
        self._cfg: Optional[CFG] = None
        self._current_block: Optional[BasicBlock] = None
        self._block_stack: List[BasicBlock] = []
        self._logger = logging.getLogger(__name__)
    
    def build(self, target: Any) -> CFG:
        """
        Build CFG from instructions, ParseResult, AST, or code string
        
        Args:
            target: List of instructions, ParseResult, ast.AST, or code string
            
        Returns:
            Built CFG
        """
        try:
            self._cfg = CFG()
            self._current_block = None
            self._block_stack = []
            
            # Check if AST or source code
            tree = None
            if isinstance(target, str):
                try:
                    tree = ast.parse(target)
                except Exception:
                    tree = None
            elif hasattr(target, 'tree') and target.tree is not None:
                tree = target.tree
            elif isinstance(target, ast.AST):
                tree = target
            elif hasattr(target, 'nodes') and target.nodes:
                tree = ast.Module(body=list(target.nodes), type_ignores=[])
            
            if tree is not None:
                ast_builder = ASTCFGBuilder(self._cfg)
                return ast_builder.build_from_ast(tree)
            
            # Otherwise process instructions
            instructions = target if isinstance(target, list) else []
            
            # Create entry block
            entry_block = BasicBlock(
                id=0,
                node_type=NodeType.ENTRY,
                instructions=[],
                line_number=1
            )
            self._cfg.add_block(entry_block)
            self._cfg.set_entry(0)
            self._current_block = entry_block
            
            # Process instructions
            for i, instr in enumerate(instructions):
                self._process_instruction(instr, i)
            
            # Create exit blocks
            if self._current_block:
                exit_block = BasicBlock(
                    id=len(self._cfg.blocks),
                    node_type=NodeType.RETURN,
                    instructions=[],
                    is_exit=True,
                    line_number=len(instructions) + 1
                )
                self._cfg.add_block(exit_block)
                self._cfg.set_exit(len(self._cfg.blocks) - 1)
                self._current_block.add_successor(len(self._cfg.blocks) - 1)
            
            # Analyze CFG
            self._cfg.find_loops()
            self._cfg.compute_dominators()
            self._cfg.compute_post_dominators()
            self._cfg.compute_dominance_frontier()
            
            self._logger.info(f"Built CFG with {len(self._cfg.blocks)} blocks")
            
            return self._cfg
            
        except Exception as e:
            self._logger.error(f"CFG build error: {e}")
            raise
    
    def _process_instruction(self, instr: Any, index: int) -> None:
        """Process a single instruction"""
        try:
            opcode = getattr(instr, 'opcode', None)
            
            # Jump instructions create new blocks
            if opcode in (0x04, 0x05, 0x06):  # JMP, JMP_IF_ZERO, JMP_IF_NOT_ZERO
                self._create_jump_block(instr, index)
            
            # Return creates exit
            elif opcode == 0x07:  # HALT/RETURN
                self._create_return_block(instr, index)
            
            # Otherwise continue current block
            else:
                if self._current_block:
                    self._current_block.instructions.append(
                        f"{instr.opcode:02X} {instr.operand}"
                    )
                    
        except Exception as e:
            self._logger.error(f"Instruction process error: {e}")
            raise
    
    def _create_jump_block(self, instr: Any, index: int) -> None:
        """Create a new block for jump instruction"""
        try:
            # Pop current block
            if self._current_block:
                self._block_stack.append(self._current_block)
            
            # Create new block
            new_block = BasicBlock(
                id=len(self._cfg.blocks),
                node_type=NodeType.JUMP,
                instructions=[f"{instr.opcode:02X} {instr.operand}"],
                line_number=index + 1
            )
            self._cfg.add_block(new_block)
            self._current_block = new_block
            
        except Exception as e:
            self._logger.error(f"Jump block creation error: {e}")
            raise
    
    def _create_return_block(self, instr: Any, index: int) -> None:
        """Create a return block"""
        try:
            # Pop current block
            if self._current_block:
                self._block_stack.append(self._current_block)
            
            # Create return block
            new_block = BasicBlock(
                id=len(self._cfg.blocks),
                node_type=NodeType.RETURN,
                instructions=[f"{instr.opcode:02X}"],
                is_exit=True,
                line_number=index + 1
            )
            self._cfg.add_block(new_block)
            self._cfg.set_exit(len(self._cfg.blocks) - 1)
            self._current_block = new_block
            
        except Exception as e:
            self._logger.error(f"Return block creation error: {e}")
            raise
    
    def get_cfg(self) -> Optional[CFG]:
        """Get built CFG"""
        return self._cfg


# Singleton instance
_builder_instance: Optional[CFGBuilder] = None


def get_cfg_builder() -> CFGBuilder:
    """Get or create CFG builder singleton"""
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = CFGBuilder()
    return _builder_instance


if __name__ == "__main__":
    # Test CFG builder
    from orthos.compiler.packer import Instruction
    
    # Create test instructions
    instructions = [
        Instruction(0x01, 0, "IMMEDIATE"),  # HALT (entry)
        Instruction(0x02, 1, "IMMEDIATE"),  # MOV
        Instruction(0x03, 2, "IMMEDIATE"),  # LOAD_CONST
        Instruction(0x04, 3, "IMMEDIATE"),  # JMP
        Instruction(0x02, 4, "IMMEDIATE"),  # MOV (after jump)
        Instruction(0x07, 0, "IMMEDIATE"),  # HALT
    ]
    
    builder = get_cfg_builder()
    cfg = builder.build(instructions)
    
    print(f"CFG built with {len(cfg.blocks)} blocks")
    print(f"Entry block: {cfg.entry_block}")
    print(f"Exit blocks: {cfg.exit_blocks}")
    print(f"Loop headers: {cfg.loop_headers}")
    
    for block_id, block in cfg.blocks.items():
        print(f"  Block {block_id}: {block.node_type.value}, "
              f"preds={block.predecessors}, succs={block.successors}")
    
    # Serialize
    cfg_dict = cfg.to_dict()
    print(f"\nSerialized CFG:")
    print(f"  Blocks: {cfg_dict['num_blocks']}")
    print(f"  Edges: {cfg_dict['num_edges']}")
