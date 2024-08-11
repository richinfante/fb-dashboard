from .util import eval_padding


class SimpleFlexBox:
    def __init__(
        self,
        identifier,
        children=[],
        flex_direction="row",
        weight=1,
        padding=(0, 0, 0, 0),
        gap=0,
    ):
        """
        An exceptionally simple flex box implementation, with no support for wrapping or alignment. All items are stretched to fill the available space, and the flex direction is either row or column.

        Each item is given a weight, which determines how much space it should take up relative to the other items. The weight is a positive float, and the total weight of all items in the flex box should be the same.

        - padding: a tuple of 4 values, representing the padding in the order of top, right, bottom, left. Each value can be an integer, a percentage string, or a vw/vh string.
        """
        self.identifier = identifier
        self.flex_direction = flex_direction
        self.children = children
        self.weight = weight
        self.gap = gap

        if isinstance(padding, (str, int)):
            self.padding = (padding, padding, padding, padding)
        elif isinstance(padding, tuple):
            if len(padding) == 2:
                self.padding = (padding[0], padding[1], padding[0], padding[1])
            elif len(padding) == 4:
                self.padding = padding

        self.computed_rect = None
        self.computed_content_rect = None

    def compute_sizes(self, x, y, width, height, root_size=None):
        out = {}

        if root_size is None:
            root_size = (width, height)

        # Compute the size of the box
        weight_sum = sum(child.weight for child in self.children)

        available_width = (
            width
            - eval_padding(self.padding[1], width, root_size)
            - eval_padding(self.padding[3], width, root_size)
        )
        available_height = (
            height
            - eval_padding(self.padding[0], height, root_size)
            - eval_padding(self.padding[2], height, root_size)
        )

        self.computed_rect = (round(x), round(y), round(width), round(height))
        self.computed_content_rect = (
            round(x + eval_padding(self.padding[3], width, root_size)),
            round(y + eval_padding(self.padding[0], height, root_size)),
            round(available_width),
            round(available_height),
        )

        out[self.identifier] = {
            "box": self.computed_rect,
            "content_box": self.computed_content_rect,
        }

        if self.flex_direction == "row":
            available_width -= (len(self.children) - 1) * eval_padding(
                self.gap, width, root_size
            )
        elif self.flex_direction == "column":
            available_height -= (len(self.children) - 1) * eval_padding(
                self.gap, height, root_size
            )

        x = x + eval_padding(self.padding[3], width, root_size)
        y = y + eval_padding(self.padding[0], height, root_size)

        for child in self.children:
            if self.flex_direction == "row":
                allocated_width = available_width * child.weight / weight_sum
                allocated_height = available_height

                out.update(
                    child.compute_sizes(
                        x, y, allocated_width, allocated_height, root_size=root_size
                    )
                )

                x += allocated_width + eval_padding(self.gap, width, root_size)

            elif self.flex_direction == "column":
                allocated_width = available_width
                allocated_height = available_height * child.weight / weight_sum

                out.update(
                    child.compute_sizes(
                        x, y, allocated_width, allocated_height, root_size=root_size
                    )
                )

                y += allocated_height + eval_padding(self.gap, height, root_size)

        return out
