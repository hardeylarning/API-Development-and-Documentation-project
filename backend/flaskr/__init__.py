import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.order_by(Category.type).all()
        if len(categories) < 1:
            abort(404)
        return jsonify({
            "success": True,
            'categories': {category.id: category.type for category in categories}
        })

    @app.route('/questions')
    def retrieve_questions():
        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)
        categories = Category.query.order_by(Category.type).all()
        total_questions = len(questions)

        if total_questions < 1:
            abort(404)
        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": total_questions,
            "current_category": None,
            "categories": [category.type for category in categories]
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(question_id == Question.id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_or_search_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        search = body.get('searchTerm', None)
        try:
            if search is not None:
                questions = Question.query.filter(Question.question.ilike('%{}%'.format(search))).all()
                current_questions = [question.format() for question in questions]
                return jsonify({
                    "success": True,
                    "questions": current_questions,
                    "total_questions": len(current_questions)
                })

            if new_answer is None or new_question is None:
                abort(422)
            question = Question(question=new_question, answer=new_answer,
                                category=new_category, difficulty=new_difficulty)
            question.insert()
            return jsonify({
                "success": True
            })
        except:
            abort(422)

    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        # adding 1 to the category id because frontend start category from 0 instead of 1
        category_id = category_id + 1
        current_category = Category.query.filter(Category.id == category_id).one_or_none()
        if current_category is None:
            abort(404)
        selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)
        total_questions = len(current_questions)
        if total_questions == 0:
            abort(404)
        return jsonify({
            "success": True,
            "questions": current_questions,
            "total_questions": total_questions,
            "current_category": current_category.type
        })

    @app.route('/quizzes', methods=['POST'])
    def generate_random_quiz():
        body = request.get_json()
        try:
            previous_questions = body.get('previous_questions', None)
            quiz_category = body.get('quiz_category', None)
            category_id = quiz_category['id']

            if category_id < 1:
                questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
            else:
                questions = Question.query.filter(
                    Question.id.notin_(previous_questions),
                    Question.category == category_id
                ).all()
            question = None
            if questions:
                question = random.choice(questions)
            return jsonify({
                "success": True,
                "question": question.format()
            })
        except:
            abort(422)

    # Errors Handler
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(500)
    def internal_server(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    return app
