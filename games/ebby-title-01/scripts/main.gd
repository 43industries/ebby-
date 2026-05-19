extends Node2D

## EBBY Title 01 — week-1 grey-box core loop.
##
## Pillar: one screen, one verb (click), one win condition (10 hits).
## Tune `win_score` and target size in the inspector during playtest.

@export var win_score: int = 10

var score: int = 0

@onready var target: ColorRect = $Target
@onready var score_label: Label = $UI/ScoreLabel
@onready var hint_label: Label = $UI/HintLabel


func _ready() -> void:
	randomize()
	_place_target()
	_update_ui()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("retry"):
		_reset()
		return

	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		if score >= win_score:
			_reset()
			return
		if target.get_global_rect().has_point(event.position):
			_hit()


func _hit() -> void:
	score += 1
	_place_target()
	_update_ui()


func _place_target() -> void:
	var view := get_viewport_rect().size
	var w := target.size.x
	var h := target.size.y
	target.position = Vector2(
		randf_range(40.0, view.x - w - 40.0),
		randf_range(80.0, view.y - h - 40.0),
	)


func _update_ui() -> void:
	if score >= win_score:
		score_label.text = "You win!"
		hint_label.text = "Click anywhere or press R to play again."
	else:
		score_label.text = "Hits: %d / %d" % [score, win_score]
		hint_label.text = "Click the purple square. R to retry."


func _reset() -> void:
	score = 0
	_place_target()
	_update_ui()
