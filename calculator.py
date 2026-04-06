#!/usr/bin/env python3
"""
CLI 计算器 - 支持加、减、乘、除运算
"""

import argparse
import sys


class Calculator:
    """计算器类，实现基本的数学运算"""
    
    @staticmethod
    def add(a, b):
        """加法运算"""
        return a + b
    
    @staticmethod
    def subtract(a, b):
        """减法运算"""
        return a - b
    
    @staticmethod
    def multiply(a, b):
        """乘法运算"""
        return a * b
    
    @staticmethod
    def divide(a, b):
        """除法运算"""
        if b == 0:
            raise ValueError("错误：除数不能为零")
        return a / b


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='CLI 计算器 - 支持加、减、乘、除运算',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例：
  python calculator.py add 5 3          # 输出: 8
  python calculator.py subtract 10 4    # 输出: 6
  python calculator.py multiply 6 7     # 输出: 42
  python calculator.py divide 8 2       # 输出: 4.0
  python calculator.py divide 5 0       # 输出: 错误信息
        '''
    )
    
    parser.add_argument(
        'operation',
        choices=['add', 'subtract', 'multiply', 'divide'],
        help='运算类型: add(加), subtract(减), multiply(乘), divide(除)'
    )
    
    parser.add_argument(
        'a',
        type=float,
        help='第一个操作数'
    )
    
    parser.add_argument(
        'b',
        type=float,
        help='第二个操作数'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细的运算过程'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    calc = Calculator()
    
    try:
        # 根据操作类型执行相应的运算
        if args.operation == 'add':
            result = calc.add(args.a, args.b)
            op_symbol = '+'
        elif args.operation == 'subtract':
            result = calc.subtract(args.a, args.b)
            op_symbol = '-'
        elif args.operation == 'multiply':
            result = calc.multiply(args.a, args.b)
            op_symbol = '*'
        elif args.operation == 'divide':
            result = calc.divide(args.a, args.b)
            op_symbol = '/'
        
        # 输出结果
        if args.verbose:
            print(f"{args.a} {op_symbol} {args.b} = {result}")
        else:
            print(result)
            
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
