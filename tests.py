import unittest
import Parser as p


class MyTestCase(unittest.TestCase):
    def test_hierarchy_arithm(self):
        self.assertEqual(p.parse("0&5+5*4", False), [0])
        self.assertEqual(p.parse("(1&5)+4==4*1.25", False), [1])
        self.assertEqual(p.parse("3**3-1", False), [26])
        self.assertEqual(p.parse("3**(3-1)", False), [9])
        self.assertEqual(p.parse("3**(3-1)+mul(2,3,sum(2,2))", False), [33])

    def test_multiple_inputs(self):
        self.assertEqual(p.parse("0&5+5*4;(1&5)+4==4*1.25", False), [0, 1])

    def test_asigning(self):
        self.assertEqual(p.parse("x:4;x;rm x", False), [4])
        self.assertEqual(p.parse("x:4+2; x; rm x", False), [6])
        self.assertEqual(p.parse("f x y: 4+x-y+2;f(3,2); rm f", False), [7])
        self.assertEqual(p.parse("f:[1,2,3]; f; rm f", False), [[1, 2, 3]])
        self.assertEqual(p.parse("f:range(3); f; rm f", False), [[0, 1, 2]])

    def test_saving_loading(self):
        self.assertIsNotNone(p.parse("save test", False))
        self.assertIsNotNone(p.parse("load test", False))

    def test_saving_loading_correctness(self):
        self.assertIsNone(p.parse("g:0&5+5*4; load test; g; rm g", False))
        self.assertEqual(p.parse("g:5; save test; load test; g; rm g", False), [5])

    def test_list_generation(self):
        self.assertEqual(p.parse("g:[i+j if i+j<=3 else 0*3 for i,j in range(3), [0,1,2]]; g; rm g", False), [[0, 2, 0]])
        self.assertEqual(p.parse("g:[i+j if i+j<=3 else 0*3 for i,j in [i for i in range(3)], [0,1,2]]; g; rm g", False), [[0, 2, 0]])

    def test_inner_cmds(self):
        self.assertIsNone(p.parse("3+i", False))
        self.assertEqual(p.parse("3+i{addv i 2}; rm i", False), [5])
        self.assertEqual(p.parse("3+i{addv i 2{j:3}}; rm i; rm j", False), [5])
        self.assertEqual(p.parse("j+i{addv i 2; addv j 4}; rm i; rm j", False), [6])
        self.assertIsNotNone(p.parse("[{ls var} for i in range(5)]", False))
        self.assertIsNotNone(p.parse("[{ls var}{ls udf} for i in range(5)]", False))

    def test_indexing(self):
        self.assertIsNone(p.parse("g:range(5); g[5]; rm g", False))
        self.assertIsNone(p.parse("rm g; g:range(5); g[-6]; rm g", False))
        self.assertEqual(p.parse("rm g; g:range(5); g[-2]+g[2]; rm g", False), [5])

    def test_indexed_assignment(self):

        self.assertEqual(p.parse("g:range(5); g[1]:2; g[1]; rm g", False), [2])


    def test_parameter_in_inner_cmd(self):
        self.assertEqual(p.parse("g:[\"qwertyu\"]; [{$i:$j*2} for i,j in g, range(5)]; [q,w,r,t]; rm g; rm q; rm w; rm r; rm t", False), [[], [0.0, 2.0, 6.0, 8.0]])


    def test_func_variable_dynamicness(self):
        self.assertEqual(p.parse("g:3; addf f x x+g; f(1); g:4; f(1); rm g; rm f", False), [4, 5])
        self.assertEqual(p.parse("g:3; f:g; g:5; f; rm g; rm f", False), [5])
        self.assertEqual(p.parse("g:3; f:=g; g:5; f; rm g; rm f", False), [3])


    def test_mic(self):
        self.assertEqual(p.parse("-(12)", False), [-12])
        self.assertEqual(p.parse("--(12)", False), [12])
        self.assertEqual(p.parse("-(-12)", False), [12])

if __name__ == '__main__':
    unittest.main()
