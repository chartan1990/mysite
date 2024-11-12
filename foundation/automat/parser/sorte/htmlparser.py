from foundation.automat.parser.parser import Parser

class Htmlparser(Parser):
    """
https://www.w3.org/1998/Math/MathML/

Example (this is similiar to latex...)

<img src="https://wikimedia.org/api/rest_v1/media/math/render/svg/95b72ff2accd775d082d041434acf09b4b7523f4" class="mwe-math-fallback-image-inline mw-invert skin-invert" aria-hidden="true" style="vertical-align: -6.171ex; width:22.568ex; height:13.509ex;" alt="{\displaystyle {\begin{aligned}I_{\text{E}}&amp;=I_{\text{ES}}\left(e^{\frac {V_{\text{BE}}}{V_{\text{T}}}}-1\right)\\I_{\text{C}}&amp;=\alpha _{\text{F}}I_{\text{E}}\\I_{\text{B}}&amp;=\left(1-\alpha _{\text{F}}\right)I_{\text{E}}\end{aligned}}}">
<img alt=alt="{\displaystyle {\begin{aligned}I_{\text{E}}&amp;=I_{\text{ES}}\left(e^{\frac {V_{\text{BE}}}{V_{\text{T}}}}-1\right)\\I_{\text{C}}&amp;=\alpha _{\text{F}}I_{\text{E}}\\I_{\text{B}}&amp;=\left(1-\alpha _{\text{F}}\right)I_{\text{E}}\end{aligned}}}">
    

https://developer.mozilla.org/en-US/docs/Web/MathML/Element/math
    """
    def __init__(self, equationStr, verbose=False):
        self._eqs = equationStr
        self.verbose = verbose
