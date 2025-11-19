import sys

from crossword import *

from collections import deque

import math

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Create a set of all the keys in self.domain to iterate over
        variables = set(self.domains.keys())
        for var in variables:
            
            # Domain is a copy of the current words inside of the variable we are iterating over
            domain = self.domains[var].copy()

            # For each word in the variable
            for word in self.domains[var]:

                # If the length of the word is less then the length of the variable
                if len(word) != var.length:
                    # Discard that work from consideration
                    domain.discard(word)
            # Update self.domains with the domain variable we created 
            self.domains[var] = domain
        
    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # If the function changes the domain of x,
        # Revised will be set to true
        revised = False  

        # Find the overlap between the nodes x and y
        overlap = self.crossword.overlaps[x, y] 

        # If there is an overlap
        if overlap:

            # Save the values that overlap
            v1, v2 = overlap

            # Create a set of words to remove
            remove = set() 

            # For each word in the domain of the variable x
            for i in self.domains[x]:

                overlaps = False  

                # For each word in the domain of the variable y
                for j in self.domains[y]:

                    # If the words aren't the same, and the letters match, 
                    # set overlap to true and break from the loop
                    if i != j and i[v1] == j[v2]:
                        overlaps = True
                        break
                # if there is no overlap in variables, remove x variable
                if not overlaps: 
                    remove.add(i)
            # if there are x variables to remove from the x domain, remove whatever is in remove
            if remove:
                self.domains[x] = self.domains[x].difference(remove)
                # set revised to true to shows that a revision was made
                revised = True
        return revised



    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If arcs is none, create a queue with every edge in the problem
        if arcs is None:  

            # Create the queue with the help of the deque module
            arcs = deque()

            # Each arc is a tuple
            # Use a nested for loop to initalize the queue with all the edge in the problem
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    arcs.appendleft((v1, v2))
        # Else, just convert the list of given arcs to a queue
        else:  
            arcs = deque(arcs)
        # While arcs is not empty
        while arcs:

            # Pop the 2 variables that make up the edge
            x, y = arcs.pop()

            # Use the revise function we wrote earlier on each combination of nodes in an edge
            if self.revise(x, y):
                # if there are no variables for x, return False, meaning that arc
                # consistency is impossible
                if len(self.domains[x]) == 0:
                    return False

                # take all x's neighbors except y and add the edges between them and x to the queue
                for z in self.crossword.neighbors(x) - {y}:
                    arcs.appendleft((z, x))
        return True
    
    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # Check if each word in variables is accounted for in assignment
        return all(variable in assignment for variable in self.crossword.variables)
    
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # For each variable and word in assignment
        for x, i, in assignment.items():

            # Check if the word is the correct length 
            if x.length != len(i):
                return False
            
            # For each variable and word in assignment
            for y, j in assignment.items():

                # If the variables aren't the same
                if x != y:

                    # If the words are the same, return false
                    if i == j:
                        return False
                    
                    # Check if the two variables overlap
                    overlap = self.crossword.overlaps[x, y]
                    if overlap:
                        a, b = overlap
                        # If the characters aren't consistent, return false
                        if i[a] != j[b]:
                            return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # find all neighbors of the given variable
        neighbors = self.crossword.neighbors(var)
        # for each variable in assignment
        for variable in assignment:
            # If variable is in neighbor
            if variable in neighbors:
                # Remove the variable from neighbor
                neighbors.remove(variable)
        # Create a list of results
        result = []
        # For each word in the variables domain
        for word in self.domains[var]:
            # Keep a count of all values that will be ruled out
            ruled_out = 0  

            # Iterate over every neighbor that the variable has
            for neighbor in neighbors:

                # Iterate every word that the neighbor variable has
                for word2 in self.domains[neighbor]:

                    # Find the overlap between the variable and the neighbors
                    overlap = self.crossword.overlaps[var, neighbor]

                    # If there is overlap between variables,
                    # Then the one of them can't have that domain anymore
                    if overlap:
                        a, b = overlap
                        if word[a] != word2[b]:
                            ruled_out += 1
            # store the variable with the number of options it will rule out from its neighbors
            result.append([word, ruled_out])
        # sort all variables by the number of ruled out domain options they will eliminate
        result.sort(key = lambda x: x[1])

        # return only the list of variables, ordered by the number of values they rule out for neighboring variables
        return [i[0] for i in result]  

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # initialize a list of potential variables to consider with heuristics (minimum remaining value and degree)
        potential_variables = []
        for variable in self.crossword.variables:  # iterate over all variables in the crossword
            if variable not in assignment:  # if the variable is unassigned (meaning it is not in assignment)
                # then add it to potentials with the number of domain options (minimum remaining value heuristic)
                # and number of neighbors (degree heuristic)
                potential_variables.append([variable, len(self.domains[variable]), len(self.crossword.neighbors(variable))])

        # sort potential variables by the number of domain options (ascending) and number of neighbors (descending)
        if potential_variables:
            potential_variables.sort(key=lambda x: (x[1], -x[2]))
            return potential_variables[0][0]

        # If there are no potential variables, simply return None
        return None


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do` so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        # If the assignment is complete, then just return assignment
        if self.assignment_complete(assignment):
            return assignment
        # Find an unassigned variable not apart of assignment
        var = self.select_unassigned_variable(assignment)
        # Use the order_domain_values we wrote earlier to iterate over the values of var
        for value in self.order_domain_values(var, assignment):

            # Add an item to assignment with the key of var and the value of value
            assignment[var] = value

            # If assignment is consistent then recursivly call backstrack to fill out the rest of assignment
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result:
                    return result
            # Else remove var from assignment
            else:
                assignment.pop(var)

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()

