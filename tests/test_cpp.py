import textwrap
import typing as t

from mrst import cpp as cpp_mod


def check_translation(
        cpp: str, rst: str, section: t.Optional[str]=None) -> None:
    output = cpp_mod.translate_cpp_file(cpp.split('\n'), section=section)

    assert '\n'.join(output) == rst


def test_simple_big_section_header():
    check_translation(
        cpp=textwrap.dedent("""
            // --------------------------------------------------
            // Hyper Module
            // --------------------------------------------------
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

            // end-doc
        """),
        rst=textwrap.dedent("""
            Hyper Module
            ------------
            This module contains hyper capabilities.
            Watch yourself!


            class Beam
            ~~~~~~~~~~
            The hyper beam is responsible for the madness.


            .. code-block:: c++

                    class Hyper {
                    public:
                        void launch_laser();
                    }


            Hyper adaptive_resonance(const Res & r);
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Returns a Hyper given the harmonic resonance.


            .. code-block:: c++

                    Hype adaptive_resonance(const Res & r);
        """).lstrip()
    )


def test_section_is_obeyed():
    check_translation(
        section='~',
        cpp=textwrap.dedent("""
            // --------------------------------------------------
            // Big Header
            // --------------------------------------------------
            //       Desc
            // --------------------------------------------------

            #include "blahblahblah"

            // --------------------------------------------------
            // section 2
            // --------------------------------------------------
            //    Desc 2
            // -------------------------------------------------/
        """),
        rst=textwrap.dedent("""
            Big Header
            ^^^^^^^^^^
            Desc


            .. code-block:: c++


                    #include "blahblahblah"

            section 2
            '''''''''
            Desc 2

        """).lstrip()
    )