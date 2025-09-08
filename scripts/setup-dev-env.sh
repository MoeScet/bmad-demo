#!/bin/bash
# Development Environment Setup Script (Unix/Linux/MacOS)
set -e

echo "🚀 Setting up BMAD development environment..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.11"

if ! python3 -c "import sys; assert sys.version_info >= (3, 11)" 2>/dev/null; then
    echo "❌ Python 3.11+ required (found $python_version)"
    exit 1
fi

# Create virtual environments for each service
for service_dir in services/*/; do
    if [ -f "$service_dir/requirements.txt" ]; then
        service_name=$(basename "$service_dir")
        echo "Setting up $service_name..."
        
        cd "$service_dir"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        deactivate
        cd - > /dev/null
        
        echo "  ✅ $service_name environment ready"
    fi
done

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Copy .env.example to .env in each service"
echo "   2. Configure database connection settings"
echo "   3. Run 'make test' to validate setup"