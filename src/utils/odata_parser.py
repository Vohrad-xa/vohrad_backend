"""OData filter parser utility for SQLAlchemy."""

from odata_query.grammar import ODataLexer, ODataParser, ast
from sqlalchemy import and_, or_
from typing import Optional


class ODataToSQLAlchemy:
    """Convert OData filter expressions to SQLAlchemy WHERE clauses."""

    def __init__(self, model_class, jsonb_fields: Optional[dict[str, str]] = None):
        """Initialize parser.

        Args:
            model_class: SQLAlchemy model class
            jsonb_fields: Dict of JSONB field names (e.g., {"specifications": "specifications"})
        """
        self.model_class  = model_class
        self.jsonb_fields = jsonb_fields or {}
        self.lexer        = ODataLexer()
        self.parser       = ODataParser()


    def parse(self, filter_expression: str):
        """Parse OData filter and return SQLAlchemy WHERE clause."""
        tokens   = self.lexer.tokenize(filter_expression)
        ast_tree = self.parser.parse(tokens)
        return self._convert_ast(ast_tree)


    def _convert_ast(self, node):
        """Convert OData AST to SQLAlchemy filter."""
        if isinstance(node, ast.Compare):
            left  = node.left
            right = node.right
            op    = node.comparator

            if isinstance(left, ast.Attribute):
                # JSONB path: e.g., specifications/cpu
                field_path = f"{left.owner.name}/{left.attr}"
                parts = field_path.split('/')

                if len(parts) == 2 and parts[0] in self.jsonb_fields:
                    jsonb_column = getattr(self.model_class, parts[0])
                    json_key = parts[1]

                    # Determine Python type for JSONB value to match JSON type semantics
                    if isinstance(right, ast.Boolean):
                        right_val: object = right.val.lower() == 'true'
                    elif hasattr(right, 'val'):
                        # Try to coerce numbers when possible, else keep string
                        val = right.val
                        try:
                            # Prefer int when exact; fallback to float
                            right_val = int(val) if str(int(val)) == str(val) else float(val)
                        except Exception:
                            right_val = str(val)
                    else:
                        right_val = str(right)

                    if isinstance(op, ast.Eq):
                        # Use JSONB containment to leverage GIN indexes
                        return jsonb_column.contains({json_key: right_val})
                    elif isinstance(op, ast.NotEq):
                        # Fallback to extracted text inequality (no GIN acceleration)
                        return jsonb_column[json_key].astext != str(right_val)

            elif isinstance(left, ast.Identifier):
                # Regular column
                field_name = left.name
                field      = getattr(self.model_class, field_name)
                right_val  = right.val if hasattr(right, 'val') else right

                # Convert OData boolean to Python boolean
                if isinstance(right, ast.Boolean):
                    right_val = right_val.lower() == 'true'

                if isinstance(op, ast.Eq):
                    return field == right_val
                elif isinstance(op, ast.NotEq):
                    return field != right_val
                elif isinstance(op, ast.Gt):
                    return field > right_val
                elif isinstance(op, ast.Lt):
                    return field < right_val
                elif isinstance(op, ast.GtE):
                    return field >= right_val
                elif isinstance(op, ast.LtE):
                    return field <= right_val

        elif isinstance(node, ast.BoolOp):
            left_filter  = self._convert_ast(node.left)
            right_filter = self._convert_ast(node.right)

            if isinstance(node.op, ast.And):
                return and_(left_filter, right_filter)
            elif isinstance(node.op, ast.Or):
                return or_(left_filter, right_filter)

        return None
