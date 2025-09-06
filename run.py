from app import create_app
import build_css

app = create_app()

if __name__ == '__main__':
    build_css.main()
    app.run(debug=True)