import textwrap
import typing as t

from mrst import cpp as cpp_mod


def fake_reader(*_args: t.Any, **_kwargs: t.Any) -> t.Tuple[t.List[str], t.Any]:
    raise AssertionError("Should not be called!")


def check_translation(
    cpp: str,
    rst: str,
    section: t.Optional[str] = None,
    reader: cpp_mod.FileReader = fake_reader,
) -> None:
    output = cpp_mod.translate_cpp_file(
        cpp.split("\n"), section=section, reader=reader
    )
    print(f"cpp={cpp}")
    formatted_rst = "\n".join(output)
    print(f"rst={formatted_rst}")
    assert "\n".join(output) == rst


def test_simple_big_section_header() -> None:
    check_translation(
        cpp=textwrap.dedent(
            """
            // --------------------------------------------------
            // Hyper Module
            // ==================================================
            //       This module contains hyper capabilities.
            //       Watch yourself!
            // -------------------------------------------------/

            #include "blahblahblah"

            // --------------------------------------------------
            // class Beam
            // --------------------------------------------------
            //    The hyper beam is responsible for the madness.
            // --------------------------------------------------
            class Hyper {
            public:
                void launch_laser();
            }


            // --------------------------------------------------
            // Hyper adaptive_resonance(const Res & r);
            // --------------------------------------------------
            //    Returns a Hyper given the harmonic resonance.
            // --------------------------------------------------
            Hype adaptive_resonance(const Res & r);

            // ~end-doc
        """
        ),
        rst=textwrap.dedent(
            """
            Hyper Module
            ============
            This module contains hyper capabilities.
            Watch yourself!

            class Beam
            ----------
            The hyper beam is responsible for the madness.

            .. code-block:: c++

                class Hyper {
                public:
                    void launch_laser();
                }

            Hyper adaptive_resonance(const Res & r);
            ----------------------------------------
            Returns a Hyper given the harmonic resonance.

            .. code-block:: c++

                Hype adaptive_resonance(const Res & r);
        """
        ).lstrip(),
    )


def test_section_is_obeyed() -> None:
    check_translation(
        section="~",
        cpp=textwrap.dedent(
            """
            // --------------------------------------------------
            // Big Header
            // ==================================================
            //       Desc
            // --------------------------------------------------

            #include "blahblahblah"

            // --------------------------------------------------
            // section 2
            // --------------------------------------------------
            //    Desc 2
            // -------------------------------------------------/
        """
        ),
        rst=textwrap.dedent(
            """
            Big Header
            ^^^^^^^^^^
            Desc

            .. code-block:: c++

                #include "blahblahblah"

            section 2
            '''''''''
            Desc 2
        """
        ).lstrip(),
    )


def test_section_header_not_necessary() -> None:
    check_translation(
        section="~",
        cpp=textwrap.dedent(
            """
            // --------------------------------------------------
            // check out this code baby:
            // --------------------------------------------------

            void nullptr int;

            // ~end-doc
        """
        ),
        rst=textwrap.dedent(
            """
            check out this code baby:

            .. code-block:: c++

                void nullptr int;
        """
        ).lstrip(),
    )


def test_code_blocks_without_text() -> None:
    check_translation(
        section="~",
        cpp=textwrap.dedent(
            """
            // ~begin-doc

            some code

            // ~end-doc

            more code

            // ~begin-doc

            even more code

            // ~end-doc
        """
        ),
        rst=textwrap.dedent(
            """
            .. code-block:: c++

                some code

            .. code-block:: c++

                even more code
        """
        ).lstrip(),
    )


def test_include_feature() -> None:
    def file_reader(
        input_file: str, **_kwargs: t.Any
    ) -> t.Tuple[t.List[str], t.Any]:
        assert input_file == "example_text.cpp"
        return (
            textwrap.dedent(
                """
                // ~begin-doc
                Thing thing;
                thing += 5;
                assert(thing.is_five());
                // ~end-doc
            """
            ).split("\n"),
            file_reader,
        )

    check_translation(
        reader=file_reader,
        cpp=textwrap.dedent(
            """
            // --------------------------------------------------
            // Thing class
            // --------------------------------------------------
            //      Oh baby, what a class this is. Let me tell
            //      you. This is a great class.
            // --------------------------------------------------
            class Thing {};

            // --------------------------------------------------
            // The following example shows how to use the is_five
            // function.
            //
            // ~see-file "example_text.cpp"
            // -------------------------------------------------/
        """
        ),
        rst=textwrap.dedent(
            """
            Thing class
            -----------
            Oh baby, what a class this is. Let me tell
            you. This is a great class.

            .. code-block:: c++

                class Thing {};

            The following example shows how to use the is_five
            function.

            .. code-block:: c++

                Thing thing;
                thing += 5;
                assert(thing.is_five());
        """
        ).lstrip(),
    )
