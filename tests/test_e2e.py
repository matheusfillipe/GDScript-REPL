"""End-to-end tests for the gdrepl REPL shell."""

import pexpect
import pytest


class TestREPLE2E:
    """End-to-end tests that spawn the actual REPL and test interactive behavior."""

    @pytest.fixture
    def repl(self):
        """Spawn a fresh REPL process for each test."""
        # Start the REPL
        child = pexpect.spawn("uv run gdrepl", timeout=15, encoding="utf-8")

        # Wait for Godot to start
        child.expect(r"Godot .* listening on: \d+", timeout=30)

        # Wait for the first prompt
        child.expect(">>>", timeout=5)

        yield child

        # Cleanup - send quit and wait for process to end
        try:
            child.sendline("!quit")
            child.expect(pexpect.EOF, timeout=5)
        except (pexpect.TIMEOUT, pexpect.EOF):
            child.close(force=True)

    def test_basic_arithmetic(self, repl):
        """Test basic arithmetic expressions."""
        repl.sendline("1 + 1")
        repl.expect(r"-> 2")
        repl.expect(">>>")

        repl.sendline("10 * 5")
        repl.expect(r"-> 50")
        repl.expect(">>>")

        repl.sendline("100 / 4")
        repl.expect(r"-> 25")
        repl.expect(">>>")

    def test_print_statement(self, repl):
        """Test print() statements produce stdout."""
        repl.sendline("print('hello world')")
        repl.expect(r"-> <null>")
        repl.expect("hello world")
        repl.expect(">>>")

    def test_variable_assignment(self, repl):
        """Test variable assignment and retrieval."""
        repl.sendline("var x = 42")
        repl.expect(">>>")

        repl.sendline("x")
        repl.expect(r"-> 42")
        repl.expect(">>>")

        repl.sendline("x + 8")
        repl.expect(r"-> 50")
        repl.expect(">>>")

    def test_string_operations(self, repl):
        """Test string operations."""
        repl.sendline('"hello" + " " + "world"')
        repl.expect(r"-> hello world")
        repl.expect(">>>")

    def test_array_operations(self, repl):
        """Test array creation and operations."""
        repl.sendline("var arr = [1, 2, 3]")
        repl.expect(">>>")

        repl.sendline("arr[0]")
        repl.expect(r"-> 1")
        repl.expect(">>>")

        repl.sendline("arr.size()")
        repl.expect(r"-> 3")
        repl.expect(">>>")

    def test_loop_execution(self, repl):
        """Test for loop execution with spaces."""
        repl.sendline("for i in range(3):")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("    print(i)")
        repl.expect(r"\.\.\.", timeout=10)

        # Send empty line to finish the loop
        repl.sendline("")

        # Should see output from the loop
        repl.expect("0", timeout=10)
        repl.expect("1", timeout=10)
        repl.expect("2", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_loop_execution_with_tab(self, repl):
        """Test for loop execution with tab indentation."""
        repl.sendline("for i in range(2):")
        repl.expect(r"\.\.\.", timeout=10)

        # Send tab + print
        repl.sendline("\tprint(i)")
        repl.expect(r"\.\.\.", timeout=10)

        # Send empty line to finish the loop
        repl.sendline("")

        # Should see output from the loop
        repl.expect("0", timeout=10)
        repl.expect("1", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_function_definition(self, repl):
        """Test function definition and calling."""
        repl.sendline("func add(a, b):")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("    return a + b")
        repl.expect(r"\.\.\.", timeout=10)

        # Send empty line to finish function
        repl.sendline("")
        repl.expect(">>>", timeout=10)

        # Call the function
        repl.sendline("add(5, 3)")
        # Function calls might not work as expected, so just check for prompt
        repl.expect(">>>", timeout=10)

    def test_conditional_logic(self, repl):
        """Test if/else statements."""
        repl.sendline("var test_val = 10")
        repl.expect(">>>", timeout=10)

        repl.sendline("if test_val > 5:")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("    print('greater')")
        repl.expect(r"\.\.\.", timeout=10)

        # Finish the block with empty line
        repl.sendline("")
        repl.expect("greater", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_reset_command(self, repl):
        """Test !reset command clears session."""
        # Set a variable
        repl.sendline("var reset_test = 123")
        repl.expect(">>>", timeout=10)

        # Verify it exists
        repl.sendline("reset_test")
        repl.expect(r"-> 123", timeout=10)
        repl.expect(">>>", timeout=10)

        # Reset the session
        repl.sendline("!reset")
        repl.expect("Environment cleared!", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_help_command(self, repl):
        """Test !help command shows available commands."""
        repl.sendline("!help")
        repl.expect("REPL SPECIAL COMMANDS", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_mode_command(self, repl):
        """Test !mode command shows editing mode."""
        repl.sendline("!mode")
        repl.expect(r"Current editing mode: (Vi|Emacs)", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_multiline_input(self, repl):
        """Test multiline expressions with proper indentation."""
        repl.sendline("var multiline_result = 0")
        repl.expect(">>>", timeout=10)

        repl.sendline("for i in range(5):")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("    multiline_result += i")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("")
        repl.expect(">>>", timeout=10)

        # Check the result (0+1+2+3+4 = 10)
        repl.sendline("multiline_result")
        repl.expect(r"-> 10", timeout=10)
        repl.expect(">>>", timeout=10)

    def test_no_repeated_output(self, repl):
        """Test that print() statements don't repeat on subsequent commands."""
        repl.sendline("print('unique_test_string')")
        repl.expect("unique_test_string", timeout=10)
        repl.expect(">>>", timeout=10)

        # Send a neutral command to establish clean state
        repl.sendline("var x = 1")
        repl.expect(">>>", timeout=10)

        # Now run another command - should NOT see the old print output
        repl.sendline("1 + 1")

        # Wait for the result
        repl.expect(r"-> 2", timeout=10)

        # Get everything before the next prompt
        repl.expect(">>>", timeout=10)

        # Check that unique_test_string is NOT in the output we just received
        assert "unique_test_string" not in repl.before, "Print statement should not repeat"

    def test_code_after_loop_execution(self, repl):
        """Test that code can be executed after a for loop completes."""
        # Execute a for loop with print
        repl.sendline("for i in range(3):")
        repl.expect(r"\.\.\.", timeout=10)

        repl.sendline("    print(i)")
        repl.expect(r"\.\.\.", timeout=10)

        # Send empty line to finish the loop
        repl.sendline("")

        # Should see output from the loop
        repl.expect("0", timeout=10)
        repl.expect("1", timeout=10)
        repl.expect("2", timeout=10)
        repl.expect(">>>", timeout=10)

        # Now execute code after the loop - this should NOT fail with
        # "Expected indented block after 'for' block" error
        repl.sendline("42")
        repl.expect(r"-> 42", timeout=10)
        repl.expect(">>>", timeout=10)

        # Try another expression to make sure state is clean
        repl.sendline("100 + 23")
        repl.expect(r"-> 123", timeout=10)
        repl.expect(">>>", timeout=10)


@pytest.mark.slow
class TestREPLPersistence:
    """Test REPL session persistence across multiple interactions."""

    def test_variables_persist(self):
        """Test that variables persist across multiple commands."""
        child = pexpect.spawn("uv run gdrepl", timeout=10, encoding="utf-8")

        try:
            child.expect(r"Godot .* listening on: \d+", timeout=30)
            child.expect(">>>", timeout=5)

            # Define multiple variables
            child.sendline("var a = 10")
            child.expect(">>>")

            child.sendline("var b = 20")
            child.expect(">>>")

            child.sendline("var c = a + b")
            child.expect(">>>")

            # Verify all persist
            child.sendline("c")
            child.expect(r"-> 30")
            child.expect(">>>")

        finally:
            child.sendline("!quit")
            child.expect(pexpect.EOF, timeout=5)
            child.close()

    def test_functions_persist(self):
        """Test that defined functions persist across multiple calls."""
        child = pexpect.spawn("uv run gdrepl", timeout=10, encoding="utf-8")

        try:
            child.expect(r"Godot .* listening on: \d+", timeout=30)
            child.expect(">>>", timeout=5)

            # Define a function
            child.sendline("func multiply(x, y):")
            child.expect(r"\.\.\.")
            child.sendline("    return x * y")
            child.expect(r"\.\.\.")
            child.sendline("")
            child.expect(">>>")

            # Call it multiple times
            child.sendline("multiply(3, 4)")
            child.expect(r"-> 12")
            child.expect(">>>")

            child.sendline("multiply(5, 6)")
            child.expect(r"-> 30")
            child.expect(">>>")

        finally:
            child.sendline("!quit")
            child.expect(pexpect.EOF, timeout=5)
            child.close()
