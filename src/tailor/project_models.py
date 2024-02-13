from pydantic import BaseModel, ConfigDict


class Sheet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    id: int
    data: dict[str, list]
    new_col_num: int
    col_names: dict[str, str]
    calculated_column_expression: dict[str, str]


class Parameter(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    value: float
    min: float
    max: float
    vary: bool


class Plot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    id: int
    data_sheet_id: int

    x_col: str
    y_col: str
    x_err_col: str | None
    y_err_col: str | None

    x_label: str
    y_label: str

    x_min: float | None
    x_max: float | None
    y_min: float | None
    y_max: float | None

    modelexpression: str
    parameters: list[Parameter]
    fit_domain: tuple[float, float] | None
    use_fit_domain: bool
    best_fit: bool

    show_initial_fit: bool
    draw_curve_option: int


class MultiPlotInfo(BaseModel):
    plot_id: int
    color: str


class MultiPlot(BaseModel):
    name: str
    id: int
    x_label: str
    y_label: str

    x_min: float | None
    x_max: float | None
    y_min: float | None
    y_max: float | None

    plots: list[MultiPlotInfo]


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    application: str
    version: str
    sheet_num: int
    plot_num: int
    sheets: list[Sheet]
    plots: list[Plot]
    multiplots: list[MultiPlot]
    tab_order: list[str]
    current_tab: int
