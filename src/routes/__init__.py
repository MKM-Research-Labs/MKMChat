# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Routes package for MKM Research Document Q&A Application.

This package contains all Flask route blueprints organized by functionality:
- summary_routes: Document summary and chat history endpoints
- chat_routes: Query processing and response generation
- index_routes: Knowledge base switching and configuration
- analysis_routes: Source analysis and visualization
"""

from .summary_routes import create_summary_blueprint
from .chat_routes import create_chat_blueprint
from .index_routes import create_index_blueprint
from .analysis_routes import create_analysis_blueprint

__all__ = [
    'create_summary_blueprint',
    'create_chat_blueprint',
    'create_index_blueprint',
    'create_analysis_blueprint'
]
